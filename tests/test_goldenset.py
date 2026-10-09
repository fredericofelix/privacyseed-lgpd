from collections import Counter

from privacyseed_lgpd.entity import Entity, Result
from privacyseed_lgpd.recognizers import validators as v
from privacyseed_lgpd.taxonomy import load_taxonomy
from scripts.evaluate import regressions, score
from scripts.goldenset import Example, Span, load_golden, parse_marked

REQUIRED_TAGS = {
    "invalid_check_digit", "phone_vs_id", "implicit_sensitive", "no_personal_data",
    "repeated_entity", "cnpj_mei",
}
CHECKS = {"cpf": v.is_valid_cpf, "cnpj": v.is_valid_cnpj, "pis": v.is_valid_pis,
          "cnh": v.is_valid_cnh, "voter_id": v.is_valid_voter_id, "credit_card": v.is_valid_card}


def test_parse_marked():
    text, spans = parse_marked("Sou [[person_name|Ana]], tenho [[sensitive_data:health|asma]].")
    assert text == "Sou Ana, tenho asma."
    assert spans == (Span("person_name", 4, 7), Span("sensitive_data", 15, 19, "health"))


def test_size_and_unique_ids():
    examples = load_golden()
    assert 60 <= len(examples) <= 100
    assert len({e.id for e in examples}) == len(examples)


def test_label_coverage():
    examples = load_golden()
    counts = Counter(s.label for e in examples for s in e.spans)
    for label in load_taxonomy().labels:
        assert counts[label] >= 5, f"{label}: {counts[label]} spans, need 5"
    subs = Counter(s.subcategory for e in examples for s in e.spans if s.subcategory)
    for sub in load_taxonomy().subcategories:
        assert subs[sub] >= 2, f"{sub}: {subs[sub]} spans, need 2"


def test_hard_case_tags_present():
    tags = {t for e in load_golden() for t in e.tags}
    assert REQUIRED_TAGS <= tags


def test_marked_identifiers_are_valid_fictional_numbers():
    for e in load_golden():
        for s in e.spans:
            if s.label in CHECKS:
                assert CHECKS[s.label](e.text[s.start : s.end]), f"{e.id}: {s.label}"


def test_spans_are_known_labels():
    tax = load_taxonomy()
    for e in load_golden():
        for s in e.spans:
            assert s.label in tax.labels
            assert (s.subcategory is None) == (s.label != "sensitive_data")


class OneShot:
    def __init__(self, result):
        self.result = result

    def analyze(self, text):
        return self.result


def test_score_counts_flagged_and_subcategories():
    ex = Example("t", "x", (Span("cnpj", 0, 5), Span("sensitive_data", 6, 9, "health")), ())
    cnpj = Entity("cnpj", "a", 0, 5, 1.0, "regex", "art5_I", check="passed")
    wrong = Entity("sensitive_data", "b", 6, 9, 1.0, "lexicon", "art5_II", "genetic", True)
    m = score([ex], OneShot(Result("x", entities=(wrong,), flagged=(cnpj,))))
    assert m["cnpj"]["tp"] == 1
    assert m["sensitive_data:health"]["fn"] == 1
    assert m["sensitive_data:genetic"]["fp"] == 1


def test_regressions():
    base = {"cpf": {"precision": 1.0, "recall": 0.9}}
    assert regressions({"cpf": {"precision": 1.0, "recall": 0.9}}, base) == []
    assert regressions({"cpf": {"precision": 0.8, "recall": 0.9}}, base) == ["cpf precision: 0.8 < baseline 1.0"]

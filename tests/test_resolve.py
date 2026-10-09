from privacyseed_lgpd.detector import redact, resolve
from privacyseed_lgpd.entity import Entity


def ent(label, start, end, score=0.9, check="none", text="x"):
    return Entity(label=label, text=text, start=start, end=end, score=score,
                  source="t", lgpd_category="art5_I", check=check)


def test_validated_identifier_beats_longer_span():
    cpf = ent("cpf", 10, 24, 1.0, "passed")
    name = ent("person_name", 0, 30, 0.99)
    kept, _ = resolve([name, cpf])
    assert kept == [cpf]


def test_longest_wins_without_validation():
    short = ent("person_name", 0, 4, 0.99)
    long = ent("address", 0, 20, 0.5)
    assert resolve([short, long])[0] == [long]


def test_score_breaks_ties():
    a = ent("person_name", 0, 10, 0.6)
    b = ent("address", 0, 10, 0.8)
    assert resolve([a, b])[0] == [b]


def test_equal_candidates_keep_input_order():
    first = ent("pis", 0, 11, 1.0, "passed")
    second = ent("cpf", 0, 11, 1.0, "passed")
    assert resolve([first, second])[0] == [first]


def test_non_overlapping_all_kept_sorted():
    a = ent("email", 20, 30)
    b = ent("phone", 0, 10)
    assert resolve([a, b])[0] == [b, a]


def test_failed_goes_to_discarded_unless_overlapping_kept():
    failed = ent("cpf", 0, 14, 0.0, "failed")
    other_failed = ent("cnh", 40, 51, 0.0, "failed")
    phone = ent("phone", 0, 14)
    kept, discarded = resolve([failed, other_failed, phone])
    assert kept == [phone]
    assert discarded == [other_failed]


def test_redact_by_offsets():
    text = "Ana, CPF 1, tel 2"
    entities = [ent("cpf", 9, 10), ent("person_name", 0, 3), ent("phone", 16, 17)]
    tags = {"cpf": "[CPF]", "person_name": "[NOME]", "phone": "[TELEFONE]"}
    assert redact(text, entities, tags) == "[NOME], CPF [CPF], tel [TELEFONE]"


def test_redact_nothing():
    assert redact("sem dados", [], {}) == "sem dados"

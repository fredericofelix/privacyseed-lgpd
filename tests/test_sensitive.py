from privacyseed_lgpd.recognizers.sensitive import SensitiveRecognizer, compile_lexicon, load_lexicon
from privacyseed_lgpd.taxonomy import load_taxonomy
from tests.fakes import FakeModel


def rec(lexicon=None, spans=None):
    return SensitiveRecognizer(model=FakeModel(spans or {}), lexicon=lexicon)


def test_lexicon_files_exist_for_every_subcategory():
    lexicon = load_lexicon()
    assert set(lexicon) == set(load_taxonomy().subcategories)
    assert all(terms for terms in lexicon.values())


def test_lexicon_matches_accent_and_case_variants():
    r = rec({"health": ["câncer"]})
    text = "Câncer, CANCER e câncer"
    found = r.find(text)
    assert [text[e.start : e.end] for e in found] == ["Câncer", "CANCER", "câncer"]


def test_lexicon_respects_word_boundaries():
    assert rec({"health": ["aids"]}).find("ajudas e laids") == []


def test_multiword_terms_allow_flexible_spacing():
    found = rec({"genetic": ["exame de DNA"]}).find("fez um exame  de DNA ontem")
    assert [e.text for e in found] == ["exame  de DNA"]


def test_entity_shape():
    e = rec({"health": ["diabetes"]}).find("tem diabetes")[0]
    assert (e.label, e.lgpd_category, e.sensitive_subcategory, e.experimental, e.source) == (
        "sensitive_data", "art5_II", "health", True, "lexicon"
    )


def test_gliner_zero_shot_maps_description_to_subcategory():
    tax = load_taxonomy()
    desc = tax.subcategories["religious_belief"].gliner_description
    text = "Ela frequenta o terreiro toda semana."
    start = text.index("frequenta o terreiro")
    spans = {desc: [{"text": "frequenta o terreiro", "confidence": 0.8, "start": start,
                     "end": start + len("frequenta o terreiro")}]}
    found = rec({}, spans).find(text)
    assert [(e.sensitive_subcategory, e.source) for e in found] == [("religious_belief", "gliner")]


def test_compile_skips_empty_subcategories():
    assert compile_lexicon({"health": [], "genetic": ["DNA"]}).keys() == {"genetic"}


def test_biometric_lexicon_needs_a_qualifier():
    # Curated by Privacy Seed: "biometria" alone often describes a system, not a person's data.
    r = SensitiveRecognizer(model=FakeModel({}))
    assert [e.text for e in r.find("O app usa biometria.") if e.sensitive_subcategory == "biometric"] == []
    found = r.find("Cadastrei a biometria facial e a biometria digital.")
    biometric = [e.text for e in found if e.sensitive_subcategory == "biometric"]
    assert biometric == ["biometria facial", "biometria digital"]

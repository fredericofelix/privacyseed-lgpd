import json

from privacyseed_lgpd.entity import Entity, Result


def _cpf_entity() -> Entity:
    return Entity(
        label="cpf", text="123.456.789-09", start=4, end=18, score=1.0,
        source="regex", lgpd_category="art5_I", check="passed",
    )


def test_entity_defaults():
    e = _cpf_entity()
    assert e.sensitive_subcategory is None
    assert e.experimental is False
    assert e.note is None


def test_result_to_json_keeps_accents_and_uses_lists():
    r = Result(anonymized="São [CPF]", entities=(_cpf_entity(),))
    raw = r.to_json()
    assert "São" in raw
    data = json.loads(raw)
    assert data["entities"][0]["check"] == "passed"
    assert data["flagged"] == [] and data["discarded"] == [] and data["warnings"] == []


def test_package_exports_version():
    import privacyseed_lgpd

    assert privacyseed_lgpd.__version__ == "0.1.0"

import warnings

import pytest

import privacyseed_lgpd.detector as detector_module
from privacyseed_lgpd import Detector
from privacyseed_lgpd.entity import Entity
from privacyseed_lgpd.recognizers.regex import RegexRecognizer


class StaticRecognizer:
    def __init__(self, entities):
        self.entities = entities

    def find(self, text):
        return list(self.entities)


def core():
    return Detector(recognizers=[RegexRecognizer()])


def test_cpf_anonymized():
    r = core().analyze("Cliente CPF 123.456.789-09.")
    assert r.anonymized == "Cliente CPF [CPF]."
    assert [e.label for e in r.entities] == ["cpf"]


def test_repeated_value_is_replaced_everywhere():
    text = "CPF 123.456.789-09; confirme o CPF 123.456.789-09."
    assert core().analyze(text).anonymized == "CPF [CPF]; confirme o CPF [CPF]."


def test_cnpj_is_flagged_not_anonymized():
    r = core().analyze("Empresa CNPJ 11.222.333/0001-81.")
    assert r.anonymized == "Empresa CNPJ 11.222.333/0001-81."
    assert r.entities == ()
    assert [e.label for e in r.flagged] == ["cnpj"]
    assert "MEI" in r.flagged[0].note


def test_cnpj_can_be_anonymized():
    r = Detector(recognizers=[RegexRecognizer()], anonymize={"cnpj"}).analyze("CNPJ 11.222.333/0001-81")
    assert r.anonymized == "CNPJ [CNPJ]"
    assert r.flagged == ()


def test_labels_filter():
    r = Detector(recognizers=[RegexRecognizer()], labels={"email"}).analyze(
        "CPF 123.456.789-09, ana@exemplo.com"
    )
    assert r.anonymized == "CPF 123.456.789-09, [EMAIL]"


def test_unknown_label_rejected():
    with pytest.raises(ValueError, match="unknown labels"):
        Detector(recognizers=[], labels={"rg"})


def test_failed_check_goes_to_discarded():
    r = core().analyze("CPF 123.456.789-00")
    assert r.anonymized == "CPF 123.456.789-00"
    assert [e.label for e in r.discarded] == ["cpf"]


def test_empty_text():
    r = core().analyze("")
    assert r.anonymized == "" and r.entities == () and r.flagged == () and r.discarded == ()


def test_sensitive_entity_uses_aggregate_tag():
    text = "tem diabetes"
    sensitive = Entity(label="sensitive_data", text="diabetes", start=4, end=12, score=1.0,
                       source="lexicon", lgpd_category="art5_II", sensitive_subcategory="health",
                       experimental=True)
    r = Detector(recognizers=[StaticRecognizer([sensitive])]).analyze(text)
    assert r.anonymized == "tem [DADO_SENSIVEL]"
    assert r.entities[0].sensitive_subcategory == "health"


def test_warns_once_without_ml(monkeypatch):
    monkeypatch.setattr(detector_module, "ml_available", lambda: False)
    monkeypatch.setattr(detector_module, "_ml_warning_shown", False)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        d1 = Detector()
        Detector()
    assert len([w for w in caught if "privacyseed-lgpd[ml]" in str(w.message)]) == 1
    assert d1.analyze("x").warnings == (detector_module.ML_MISSING,)

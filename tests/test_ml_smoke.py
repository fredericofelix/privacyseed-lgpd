"""Real-model checks. Run with: pytest -m ml"""

import pytest

pytestmark = pytest.mark.ml


def test_model_finds_a_name_with_matching_offsets():
    from privacyseed_lgpd.recognizers._model import extract, load_model

    text = "Meu nome é Ana Beatriz Rocha e moro na Rua das Acácias, 120, em Belo Horizonte."
    spans = extract(load_model(), text, ["person", "address"], 0.3)
    assert any(text[s:e] == "Ana Beatriz Rocha" for label, s, e, _ in spans if label == "person")


def test_detector_end_to_end():
    from privacyseed_lgpd import Detector

    r = Detector().analyze("João Silva, CPF 123.456.789-09, tem diabetes.")
    assert r.anonymized == "[NOME], CPF [CPF], tem [DADO_SENSIVEL]."
    assert r.warnings == ()

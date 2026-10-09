from pathlib import Path

import lgpd_views as views

from privacyseed_lgpd import Detector
from privacyseed_lgpd.recognizers.regex import RegexRecognizer

detector = Detector(recognizers=[RegexRecognizer()])


def test_truncate():
    assert views.truncate("abc") == ("abc", False)
    text, cut = views.truncate("x" * 6000)
    assert len(text) == views.MAX_CHARS and cut


def test_legal_rows_cover_entities_and_flagged():
    r = detector.analyze("CPF 123.456.789-09, CNPJ 11.222.333/0001-81")
    rows = views.legal_rows(r)
    assert rows[0][:3] == ["CPF", "Dado pessoal", "Art. 5º, I"]
    assert rows[1][0] == "CNPJ" and "MEI" in rows[1][3]
    assert all(row[4] == "Não" for row in rows)
    assert all(len(row) == len(views.LEGAL_HEADERS) for row in rows)


def test_highlighted_rebuilds_text():
    text = "CPF 123.456.789-09 e CPF 123.456.789-00"
    segments = views.highlighted(text, detector.analyze(text))
    assert "".join(s for s, _ in segments) == text
    labels = [lab for _, lab in segments if lab]
    assert labels[0].startswith("cpf") and "descartado" in labels[1]


def test_disclaimer_and_cta_verbatim():
    assert views.DISCLAIMER.startswith("**Anonimização automatizada de dados pessoais (LGPD).**")
    assert "não constitui aconselhamento jurídico" in views.DISCLAIMER
    assert "utm_source=hf-space" in views.CTA


def test_examples_load():
    examples = views.load_examples(Path(views.__file__).parent / "examples")
    assert len(examples) == 3 and all(examples)


def test_views_do_not_import_gradio():
    source = Path(views.__file__).read_text(encoding="utf-8")
    assert "import gradio" not in source and "from gradio" not in source

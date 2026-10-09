from privacyseed_lgpd.recognizers._model import extract
from privacyseed_lgpd.recognizers.gliner import GlinerRecognizer
from tests.fakes import FakeModel

TEXT = "Ana Souza mora na Rua A, 10."


def span(text, value, confidence):
    start = text.index(value)
    return {"text": value, "confidence": confidence, "start": start, "end": start + len(value)}


def test_extract_reads_offsets():
    model = FakeModel({"person": [span(TEXT, "Ana Souza", 0.9)]})
    assert extract(model, TEXT, ["person"], 0.5) == [("person", 0, 9, 0.9)]


def test_extract_drops_inconsistent_offsets():
    bad = {"text": "Ana Souza", "confidence": 0.9, "start": 2, "end": 11}
    out_of_range = {"text": "x", "confidence": 0.9, "start": 50, "end": 51}
    no_offsets = {"text": "Ana", "confidence": 0.9}
    model = FakeModel({"person": [bad, out_of_range, no_offsets]})
    assert extract(model, TEXT, ["person"], 0.5) == []


def test_maps_labels_and_applies_per_label_threshold():
    model = FakeModel({
        "person": [span(TEXT, "Ana Souza", 0.55)],
        "address": [span(TEXT, "Rua A, 10", 0.55)],
    })
    rec = GlinerRecognizer(model=model, thresholds={"person": 0.6, "address": 0.5})
    found = rec.find(TEXT)
    assert [(e.label, e.text, e.source) for e in found] == [("address", "Rua A, 10", "gliner")]
    assert found[0].lgpd_category == "art5_I"


def test_blank_text_skips_model():
    model = FakeModel({})
    assert GlinerRecognizer(model=model).find("   ") == []
    assert model.calls == 0

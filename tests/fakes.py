"""A stand-in for gliner2's GLiNER2 with the same output shape."""


class FakeModel:
    def __init__(self, spans_by_label):
        self.spans_by_label = spans_by_label
        self.calls = 0

    def extract_entities_long(self, text, labels, threshold=0.5, include_confidence=False,
                              include_spans=False, **kwargs):
        self.calls += 1
        return {
            "entities": {
                label: [s for s in self.spans_by_label.get(label, []) if s["confidence"] >= threshold]
                for label in labels
            }
        }

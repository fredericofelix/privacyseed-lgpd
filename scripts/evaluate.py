"""Score the detector on the golden set; write METRICS.md and check the baseline.

python -m scripts.evaluate                    # print metrics, write METRICS.md
python -m scripts.evaluate --write-baseline   # also write tests/golden/baseline.json
python -m scripts.evaluate --check            # exit 1 if any metric is below the baseline
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from privacyseed_lgpd import Detector
from scripts.goldenset import Example, key, load_golden

ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = ROOT / "tests" / "golden" / "baseline.json"
METRICS_PATH = ROOT / "METRICS.md"


def _ratio(a: int, b: int) -> float | None:
    return round(a / b, 3) if b else None


def score(examples: list[Example], detector) -> dict[str, dict]:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    for ex in examples:
        result = detector.analyze(ex.text)
        predicted = {(key(e.label, e.sensitive_subcategory), e.start, e.end)
                     for e in (*result.entities, *result.flagged)}
        gold = {(key(s.label, s.subcategory), s.start, s.end) for s in ex.spans}
        for k, _, _ in predicted & gold:
            counts[k]["tp"] += 1
        for k, _, _ in predicted - gold:
            counts[k]["fp"] += 1
        for k, _, _ in gold - predicted:
            counts[k]["fn"] += 1
    metrics = {}
    for k in sorted(counts):
        c = counts[k]
        p = _ratio(c["tp"], c["tp"] + c["fp"])
        r = _ratio(c["tp"], c["tp"] + c["fn"])
        f1 = round(2 * p * r / (p + r), 3) if p and r else None
        metrics[k] = {**c, "precision": p, "recall": r, "f1": f1}
    return metrics


def _fmt(x: float | None) -> str:
    return "—" if x is None else f"{x:.2f}"


def write_metrics_md(metrics: dict[str, dict], n_examples: int) -> None:
    lines = [
        "# Metrics",
        "",
        f"Golden set v0: {n_examples} fictional, author-written sentences. Small and not "
        "independent: treat these numbers as a smoke test. A full benchmark is coming.",
        "",
        "Exact span match (label + start + end). Rows starting with `sensitive_data:` are "
        "**experimental**.",
        "",
        "| Label | Precision | Recall | F1 | TP | FP | FN |",
        "|---|---|---|---|---|---|---|",
    ]
    for k, m in metrics.items():
        lines.append(f"| `{k}` | {_fmt(m['precision'])} | {_fmt(m['recall'])} | {_fmt(m['f1'])} "
                     f"| {m['tp']} | {m['fp']} | {m['fn']} |")
    METRICS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def regressions(metrics: dict[str, dict], baseline: dict[str, dict]) -> list[str]:
    problems = []
    for k, base in baseline.items():
        current = metrics.get(k, {})
        for name in ("precision", "recall"):
            if base.get(name) is not None and (current.get(name) or 0.0) < base[name]:
                problems.append(f"{k} {name}: {current.get(name)} < baseline {base[name]}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    examples = load_golden()
    metrics = score(examples, Detector())
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    write_metrics_md(metrics, len(examples))
    if args.write_baseline:
        BASELINE_PATH.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    if args.check:
        problems = regressions(metrics, json.loads(BASELINE_PATH.read_text(encoding="utf-8")))
        for p in problems:
            print("REGRESSION", p, file=sys.stderr)
        return 1 if problems else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Pure helpers for the Space UI (no gradio import, so CI tests them)."""

from __future__ import annotations

from pathlib import Path

from privacyseed_lgpd.entity import Entity, Result
from privacyseed_lgpd.taxonomy import load_taxonomy

MAX_CHARS = 5000

NOTICE = (
    "⚠️ **Não cole dados reais.** Use os exemplos sintéticos ou rode localmente com "
    "`pip install 'privacyseed-lgpd[ml]'`. O texto é processado só em memória e não é guardado."
)

DISCLAIMER = (
    "**Anonimização automatizada de dados pessoais (LGPD).** A ferramenta detecta e remove "
    "dados pessoais por meio de modelos de IA e regras. Nenhum método automatizado identifica "
    "100% dos dados, e a combinação de informações indiretas pode permitir a reidentificação. "
    "Se o resultado constitui dado anonimizado nos termos do art. 12 da LGPD depende de uma "
    "análise do contexto e dos meios razoavelmente disponíveis para reverter o processo. "
    "Revise sempre a saída. Esta ferramenta não constitui aconselhamento jurídico."
)

CTA = (
    "Precisa validar a anonimização dos seus dados? [Fale com a Privacy Seed]"
    "(https://www.privacyseed.com.br/?utm_source=hf-space&utm_medium=space&utm_campaign=lgpd-detector)."
)

USAGE = """pip install 'privacyseed-lgpd[ml]'

from privacyseed_lgpd import Detector

result = Detector().analyze(texto)
print(result.anonymized)
print(result.to_json(indent=2))"""

LEGAL_HEADERS = ["Tipo", "Categoria LGPD", "Artigo", "Nota", "Experimental?"]

_CATEGORY = {"art5_I": "Dado pessoal", "art5_II": "Dado pessoal sensível"}


def truncate(text: str) -> tuple[str, bool]:
    return (text[:MAX_CHARS], True) if len(text) > MAX_CHARS else (text, False)


def _type_name(e: Entity) -> str:
    tax = load_taxonomy()
    name = tax.labels[e.label].name
    if e.sensitive_subcategory:
        return f"{name} ({tax.subcategories[e.sensitive_subcategory].wording})"
    return name


def _row(e: Entity, flagged: bool) -> list[str]:
    info = load_taxonomy().labels[e.label]
    note = e.note or info.note or ""
    return [
        _type_name(e),
        _CATEGORY[e.lgpd_category],
        info.article,
        note if flagged or note else "",
        "Sim" if e.experimental else "Não",
    ]


def legal_rows(result: Result) -> list[list[str]]:
    rows = [(e.start, _row(e, False)) for e in result.entities]
    rows += [(e.start, _row(e, True)) for e in result.flagged]
    return [row for _, row in sorted(rows, key=lambda item: item[0])]


def highlighted(text: str, result: Result) -> list[tuple[str, str | None]]:
    marks = [(e, "") for e in result.entities]
    marks += [(e, " · sinalizado") for e in result.flagged]
    marks += [(e, " · descartado") for e in result.discarded]
    segments: list[tuple[str, str | None]] = []
    cursor = 0
    for e, suffix in sorted(marks, key=lambda m: m[0].start):
        if e.start > cursor:
            segments.append((text[cursor : e.start], None))
        segments.append((text[e.start : e.end], f"{e.label} · {e.source} · {e.score:.2f}{suffix}"))
        cursor = e.end
    if cursor < len(text):
        segments.append((text[cursor:], None))
    return segments


def load_examples(folder: Path) -> list[str]:
    return [p.read_text(encoding="utf-8").strip() for p in sorted(folder.glob("*.txt"))]

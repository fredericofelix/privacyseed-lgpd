"""Regex recognizer: identifiers with check digits, contact data, dates of birth."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from ..entity import Entity
from ..taxonomy import load_taxonomy
from . import validators as v

CONTEXT_WINDOW = 40  # characters before a match searched for a trigger word
FAILED_NOTE = "Dígito verificador inválido: mantido no texto para revisão."

# A match may not start or end inside a longer token ("123.456.789-09" at the
# end of a sentence is fine; "0012345678909" is not a CPF).
_START = r"(?<![\w./-])"
_END = r"(?![\w]|[./-]\w)"


def _rx(body: str) -> re.Pattern[str]:
    return re.compile(_START + body + _END)


def _ctx(body: str) -> re.Pattern[str]:
    return re.compile(body, re.IGNORECASE)


def _valid_birth_date(value: str) -> bool:
    day, month, year = (int(p) for p in re.split(r"[/.-]", value))
    try:
        born = date(year, month, day)
    except ValueError:
        return False
    return 1900 <= born.year and born <= date.today()


@dataclass(frozen=True)
class Pattern:
    label: str
    regex: re.Pattern[str]
    validate: Callable[[str], bool] | None = None  # check digit
    accept: Callable[[str], bool] | None = None  # format filter; failing drops silently
    context: re.Pattern[str] | None = None
    discard_on_fail: bool = True  # False: a failed check drops silently (bare digit runs)


# Order matters for ties (same span, same score): context-specific patterns first.
PATTERNS: tuple[Pattern, ...] = (
    Pattern("pis", _rx(r"\d{3}\.\d{5}\.\d{2}-\d"), v.is_valid_pis),
    Pattern("pis", _rx(r"\d{11}"), v.is_valid_pis, context=_ctx(r"\b(PIS|PASEP|NIS|NIT)\b")),
    Pattern("cnh", _rx(r"\d{11}"), v.is_valid_cnh,
            context=_ctx(r"\bCNH\b|carteira de (motorista|habilita[çc][ãa]o)|habilita[çc][ãa]o")),
    Pattern("voter_id", _rx(r"\d{4}\s?\d{4}\s?\d{4}"), v.is_valid_voter_id,
            context=_ctx(r"t[íi]tulo( de)? eleitor|t[íi]tulo eleitoral|inscri[çc][ãa]o eleitoral")),
    Pattern("cpf", _rx(r"\d{3}\.\d{3}\.\d{3}-\d{2}"), v.is_valid_cpf),
    Pattern("cpf", _rx(r"\d{11}"), v.is_valid_cpf, discard_on_fail=False),
    Pattern("cnpj", _rx(r"[0-9A-Za-z]{2}\.[0-9A-Za-z]{3}\.[0-9A-Za-z]{3}/[0-9A-Za-z]{4}-\d{2}"),
            v.is_valid_cnpj),
    Pattern("cnpj", _rx(r"\d{14}"), v.is_valid_cnpj, discard_on_fail=False),
    Pattern("credit_card", _rx(r"\d{4}(?:[ -]\d{4}){3}|\d{4}[ -]\d{6}[ -]\d{5}"), v.is_valid_card),
    Pattern("credit_card", _rx(r"\d{13,19}"), v.is_valid_card,
            context=_ctx(r"cart[ãa]o|cr[ée]dito|d[ée]bito")),
    Pattern("email", re.compile(r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    Pattern("phone", _rx(r"(?:\+55[\s-]?)?(?:\(\d{2}\)\s?|\d{2}[\s-])9?\d{4}[\s-]?\d{4}"),
            accept=v.is_valid_phone),
    Pattern("phone", _rx(r"(?:\+?55)?\d{10,11}"), accept=v.is_valid_phone,
            context=_ctx(r"\btel\b|telefone|fone|celular|whats")),
    Pattern("cep", _rx(r"\d{5}-?\d{3}"), context=_ctx(r"\bCEP\b")),
    Pattern("birth_date", _rx(r"\d{1,2}[/.-]\d{1,2}[/.-]\d{4}"), accept=_valid_birth_date,
            context=_ctx(r"nasc|\bDN\b")),
)


class RegexRecognizer:
    def __init__(self, patterns: tuple[Pattern, ...] = PATTERNS) -> None:
        self._patterns = patterns
        self._taxonomy = load_taxonomy()

    def find(self, text: str) -> list[Entity]:
        found: list[Entity] = []
        for p in self._patterns:
            for m in p.regex.finditer(text):
                value = m.group(0)
                if p.context and not p.context.search(text[max(0, m.start() - CONTEXT_WINDOW) : m.start()]):
                    continue
                if p.accept and not p.accept(value):
                    continue
                if p.validate is None:
                    check, score = "none", 0.9
                elif p.validate(value):
                    check, score = "passed", 1.0
                elif p.discard_on_fail:
                    check, score = "failed", 0.0
                else:
                    continue
                found.append(
                    Entity(
                        label=p.label,
                        text=value,
                        start=m.start(),
                        end=m.end(),
                        score=score,
                        source="regex",
                        lgpd_category=self._taxonomy.labels[p.label].lgpd_category,
                        check=check,
                        note=FAILED_NOTE if check == "failed" else None,
                    )
                )
        return found

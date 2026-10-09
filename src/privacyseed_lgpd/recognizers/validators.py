"""Check-digit validators for Brazilian identifiers and payment cards.

Each *_check_digit(s) function computes the check digits from the base, so
tests and scripts/fake_ids.py can build valid fictional numbers.
"""

from __future__ import annotations

import re

_NON_DIGIT = re.compile(r"\D")
_NON_ALNUM = re.compile(r"[^0-9A-Za-z]")
_CNPJ_BASE = re.compile(r"[0-9A-Z]{12}")

# Brazilian area codes (DDD) in use.
DDDS = frozenset(
    [*range(11, 20), 21, 22, 24, 27, 28, 31, 32, 33, 34, 35, 37, 38, *range(41, 50),
     51, 53, 54, 55, *range(61, 70), 71, 73, 74, 75, 77, 79, *range(81, 90), *range(91, 100)]
)

# Título de eleitor state codes: 01 (SP) to 28 (abroad).
_VOTER_STATES = range(1, 29)


def digits(value: str) -> str:
    return _NON_DIGIT.sub("", value)


def _repeated(value: str) -> bool:
    return len(set(value)) == 1


def cpf_check_digits(base: str) -> str:
    nums = [int(c) for c in base]
    first = sum(d * w for d, w in zip(nums, range(10, 1, -1))) * 10 % 11 % 10
    nums.append(first)
    second = sum(d * w for d, w in zip(nums, range(11, 1, -1))) * 10 % 11 % 10
    return f"{first}{second}"


def is_valid_cpf(value: str) -> bool:
    d = digits(value)
    return len(d) == 11 and not _repeated(d) and d[9:] == cpf_check_digits(d[:9])


def cnpj_check_digits(base: str) -> str:
    # Alphanumeric CNPJ: each character is worth its ASCII code minus 48,
    # so digits keep their value and "A" is 17.
    values = [ord(c) - 48 for c in base.upper()]
    out = ""
    for weights in ([5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]):
        rest = sum(a * b for a, b in zip(values, weights)) % 11
        digit = 0 if rest < 2 else 11 - rest
        out += str(digit)
        values.append(digit)
    return out


def is_valid_cnpj(value: str) -> bool:
    v = _NON_ALNUM.sub("", value).upper()
    return (
        len(v) == 14
        and _CNPJ_BASE.fullmatch(v[:12]) is not None
        and v[12:].isdigit()
        and not _repeated(v)
        and v[12:] == cnpj_check_digits(v[:12])
    )


def pis_check_digit(base: str) -> str:
    rest = sum(int(a) * b for a, b in zip(base, [3, 2, 9, 8, 7, 6, 5, 4, 3, 2])) % 11
    return str(0 if rest < 2 else 11 - rest)


def is_valid_pis(value: str) -> bool:
    d = digits(value)
    return len(d) == 11 and not _repeated(d) and d[10] == pis_check_digit(d[:10])


def cnh_check_digits(base: str) -> str:
    nums = [int(c) for c in base]
    first = sum(d * w for d, w in zip(nums, range(9, 0, -1))) % 11
    discount = 0
    if first >= 10:
        first, discount = 0, 2
    second = sum(d * w for d, w in zip(nums, range(1, 10))) % 11 - discount
    if second < 0:
        second += 11
    if second >= 10:
        second = 0
    return f"{first}{second}"


def is_valid_cnh(value: str) -> bool:
    d = digits(value)
    return len(d) == 11 and not _repeated(d) and d[9:] == cnh_check_digits(d[:9])


def voter_check_digits(base: str, sp_mg_exception: bool = True) -> str:
    seq = [int(c) for c in base[:8]]
    state = base[8:10]
    # Some implementations give SP (01) and MG (02) a 1 instead of 0 when the rest
    # is 0; Res. TSE 23.659/2021 art. 36 does not. is_valid_voter_id accepts both.
    sp_mg = sp_mg_exception and state in ("01", "02")
    rest = sum(d * w for d, w in zip(seq, range(2, 10))) % 11
    first = 1 if rest == 0 and sp_mg else 0 if rest == 10 else rest
    rest = (int(state[0]) * 7 + int(state[1]) * 8 + first * 9) % 11
    second = 1 if rest == 0 and sp_mg else 0 if rest == 10 else rest
    return f"{first}{second}"


def is_valid_voter_id(value: str) -> bool:
    d = digits(value)
    return (
        len(d) == 12
        and not _repeated(d)
        and int(d[8:10]) in _VOTER_STATES
        and d[10:] in {voter_check_digits(d[:10]), voter_check_digits(d[:10], sp_mg_exception=False)}
    )


def luhn_check_digit(base: str) -> str:
    total = 0
    for i, c in enumerate(reversed(base)):
        n = int(c)
        if i % 2 == 0:  # doubled once the check digit is appended
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return str((10 - total % 10) % 10)


def is_valid_card(value: str) -> bool:
    d = digits(value)
    return 13 <= len(d) <= 19 and not _repeated(d) and d[-1] == luhn_check_digit(d[:-1])


def is_valid_phone(value: str) -> bool:
    d = digits(value)
    if len(d) in (12, 13) and d.startswith("55"):
        d = d[2:]
    if len(d) not in (10, 11) or int(d[:2]) not in DDDS:
        return False
    if len(d) == 11:
        return d[2] == "9"
    return d[2] in "2345"

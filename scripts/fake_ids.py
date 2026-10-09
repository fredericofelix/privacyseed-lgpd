"""Print valid fictional identifiers for the golden set and the Space examples.

The numbers are random with valid check digits and are not linked to anyone.
Usage: python -m scripts.fake_ids cpf 5
"""

from __future__ import annotations

import argparse
import random

from privacyseed_lgpd.recognizers import validators as v


def _rand(rng: random.Random, n: int) -> str:
    return "".join(rng.choice("0123456789") for _ in range(n))


def _cpf(rng):
    b = _rand(rng, 9)
    n = b + v.cpf_check_digits(b)
    return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}"


def _cnpj(rng):
    b = _rand(rng, 8) + "0001"
    n = b + v.cnpj_check_digits(b)
    return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}"


def _pis(rng):
    b = _rand(rng, 10)
    n = b + v.pis_check_digit(b)
    return f"{n[:3]}.{n[3:8]}.{n[8:10]}-{n[10]}"


def _cnh(rng):
    b = _rand(rng, 9)
    return b + v.cnh_check_digits(b)


def _voter_id(rng):
    b = _rand(rng, 8) + f"{rng.randint(1, 28):02d}"
    n = b + v.voter_check_digits(b)
    return f"{n[:4]} {n[4:8]} {n[8:]}"


def _credit_card(rng):
    b = "4" + _rand(rng, 14)
    n = b + v.luhn_check_digit(b)
    return " ".join(n[i : i + 4] for i in range(0, 16, 4))


KINDS = {
    "cpf": (_cpf, v.is_valid_cpf),
    "cnpj": (_cnpj, v.is_valid_cnpj),
    "pis": (_pis, v.is_valid_pis),
    "cnh": (_cnh, v.is_valid_cnh),
    "voter_id": (_voter_id, v.is_valid_voter_id),
    "credit_card": (_credit_card, v.is_valid_card),
}


def fake(kind: str, rng: random.Random) -> str:
    make, check = KINDS[kind]
    while True:  # retries the rare all-repeated-digits case
        value = make(rng)
        if check(value):
            return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=sorted(KINDS))
    parser.add_argument("count", type=int, nargs="?", default=1)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    for _ in range(args.count):
        print(fake(args.kind, rng))


if __name__ == "__main__":
    main()

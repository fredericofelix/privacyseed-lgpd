import random

import pytest

from privacyseed_lgpd.recognizers import validators as v
from scripts.fake_ids import KINDS, fake

CHECKS = {
    "cpf": v.is_valid_cpf,
    "cnpj": v.is_valid_cnpj,
    "pis": v.is_valid_pis,
    "cnh": v.is_valid_cnh,
    "voter_id": v.is_valid_voter_id,
    "credit_card": v.is_valid_card,
}


@pytest.mark.parametrize("kind", sorted(CHECKS))
def test_fake_values_are_valid(kind):
    rng = random.Random(7)
    for _ in range(50):
        assert CHECKS[kind](fake(kind, rng))


def test_kinds_cover_all_checks():
    assert set(KINDS) == set(CHECKS)


def test_formats():
    rng = random.Random(1)
    assert len(fake("cpf", rng)) == 14  # 000.000.000-00
    assert len(fake("cnpj", rng)) == 18  # 00.000.000/0000-00
    assert len(fake("credit_card", rng)) == 19  # 0000 0000 0000 0000

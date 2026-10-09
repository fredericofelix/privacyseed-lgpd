import random

import pytest

from privacyseed_lgpd.recognizers import validators as v


# Published vectors.
def test_cpf_known_vector():
    assert v.cpf_check_digits("123456789") == "09"
    assert v.is_valid_cpf("123.456.789-09")
    assert v.is_valid_cpf("12345678909")


def test_cnpj_known_vectors():
    assert v.cnpj_check_digits("112223330001") == "81"
    assert v.is_valid_cnpj("11.222.333/0001-81")
    assert v.is_valid_cnpj("11222333000181")


def test_cnpj_alphanumeric_vector():
    # Receita Federal example for the alphanumeric CNPJ (issued from July 2026).
    assert v.cnpj_check_digits("12ABC34501DE") == "35"
    assert v.is_valid_cnpj("12.ABC.345/01DE-35")
    assert v.is_valid_cnpj("12.abc.345/01de-35")


# Hand-computed vectors (no official vector found; arithmetic in comments).
def test_pis_hand_vector():
    # 1,2,0,4,4,5,4,5,2,2 x 3,2,9,8,7,6,5,4,3,2 = 147; 147 % 11 = 4; 11 - 4 = 7
    assert v.pis_check_digit("1204454522") == "7"
    assert v.is_valid_pis("120.44545.22-7")


def test_cnh_hand_vector():
    # first: sum(d*w, w=9..1) = 165, 165 % 11 = 0
    # second: sum(d*w, w=1..9) = 285, 285 % 11 = 10 -> 0
    assert v.cnh_check_digits("123456789") == "00"
    assert v.is_valid_cnh("12345678900")


def test_voter_id_hand_vector():
    # first: 1,0,2,3,8,5,0,1 x 2..9 = 117, 117 % 11 = 7
    # second: state 06 -> 0*7 + 6*8 + 7*9 = 111, 111 % 11 = 1
    assert v.voter_check_digits("1023850106") == "71"
    assert v.is_valid_voter_id("1023 8501 0671")


def test_voter_id_rejects_unknown_state_code():
    base = "1023850129"  # state code 29 does not exist
    assert not v.is_valid_voter_id(base + v.voter_check_digits(base))


def test_luhn():
    assert v.luhn_check_digit("411111111111111") == "1"
    assert v.is_valid_card("4111 1111 1111 1111")
    assert not v.is_valid_card("4111 1111 1111 1112")


@pytest.mark.parametrize(
    "func,value",
    [
        (v.is_valid_cpf, "123.456.789-08"),
        (v.is_valid_cnpj, "11.222.333/0001-80"),
        (v.is_valid_pis, "120.44545.22-6"),
        (v.is_valid_cnh, "12345678901"),
        (v.is_valid_voter_id, "1023 8501 0672"),
    ],
)
def test_wrong_check_digit_fails(func, value):
    assert not func(value)


@pytest.mark.parametrize(
    "func,value",
    [
        (v.is_valid_cpf, "111.111.111-11"),
        (v.is_valid_cnpj, "00.000.000/0000-00"),
        (v.is_valid_pis, "00000000000"),
        (v.is_valid_cnh, "22222222222"),
        (v.is_valid_card, "0000 0000 0000 0000"),
    ],
)
def test_repeated_digits_fail(func, value):
    assert not func(value)


@pytest.mark.parametrize(
    "func,value",
    [(v.is_valid_cpf, "123.456.789-0"), (v.is_valid_cnpj, "11.222.333/0001-8"), (v.is_valid_card, "4111")],
)
def test_wrong_length_fails(func, value):
    assert not func(value)


def test_generated_numbers_round_trip():
    rng = random.Random(42)
    for _ in range(200):
        base9 = "".join(rng.choice("0123456789") for _ in range(9))
        if len(set(base9)) > 1:
            assert v.is_valid_cpf(base9 + v.cpf_check_digits(base9))
            assert v.is_valid_cnh(base9 + v.cnh_check_digits(base9))
        base12 = "".join(rng.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(12))
        assert v.is_valid_cnpj(base12 + v.cnpj_check_digits(base12))


@pytest.mark.parametrize(
    "value",
    ["(31) 99876-5432", "31 99876-5432", "+55 31 99876-5432", "(11) 3333-4444", "5531998765432"],
)
def test_valid_phones(value):
    assert v.is_valid_phone(value)


@pytest.mark.parametrize(
    "value",
    ["(20) 99876-5432", "(31) 1234-5678", "(31) 89876-5432", "99876-5432"],
)
def test_invalid_phones(value):
    # 20 is not an area code; landlines start with 2-5; 11-digit mobiles start with 9;
    # no area code at all.
    assert not v.is_valid_phone(value)


def test_ddd_count():
    assert len(v.DDDS) == 67

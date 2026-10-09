import pytest

from privacyseed_lgpd.recognizers.base import Recognizer
from privacyseed_lgpd.recognizers.regex import RegexRecognizer

rec = RegexRecognizer()


def labels(text):
    return [(e.label, e.text, e.check) for e in rec.find(text)]


def test_is_a_recognizer():
    assert isinstance(rec, Recognizer)


def test_formatted_cpf_passes():
    assert ("cpf", "123.456.789-09", "passed") in labels("CPF 123.456.789-09.")


def test_formatted_cpf_with_wrong_digit_is_failed():
    found = rec.find("CPF 123.456.789-00")
    assert [(e.label, e.check) for e in found] == [("cpf", "failed")]
    assert "Dígito verificador" in found[0].note


def test_bare_cpf_wrong_digit_is_dropped_silently():
    assert labels("pedido 12345678900 enviado") == []


def test_bare_valid_cpf_is_found():
    assert ("cpf", "12345678909", "passed") in labels("doc 12345678909")


def test_cnpj_formats():
    assert ("cnpj", "11.222.333/0001-81", "passed") in labels("CNPJ 11.222.333/0001-81")
    assert ("cnpj", "12.ABC.345/01DE-35", "passed") in labels("CNPJ 12.ABC.345/01DE-35")


def test_no_match_inside_longer_number():
    # 20-digit protocol number contains a valid CPF (12345678909) as a substring.
    assert labels("protocolo 00012345678909000000") == []
    # 14-digit CNPJ must not also produce an 11-digit CPF candidate.
    assert [lab for lab, _, _ in labels("11222333000181")] == ["cnpj"]


def test_pis_with_context():
    assert ("pis", "12044545227", "passed") in labels("PIS 12044545227")


def test_cnh_needs_context():
    assert ("cnh", "12345678900", "passed") in labels("CNH nº 12345678900")
    assert all(lab != "cnh" for lab, _, _ in labels("código 12345678900"))


def test_voter_id_needs_context():
    assert ("voter_id", "1023 8501 0671", "passed") in labels("título de eleitor 1023 8501 0671")
    assert labels("ref 1023 8501 0671") == []


def test_card():
    assert ("credit_card", "4111 1111 1111 1111", "passed") in labels("cartão 4111 1111 1111 1111")
    assert ("credit_card", "4111 1111 1111 1112", "failed") in labels("cartão 4111 1111 1111 1112")


def test_email():
    assert ("email", "ana.souza+teste@exemplo.com.br", "none") in labels(
        "escreva para ana.souza+teste@exemplo.com.br."
    )


@pytest.mark.parametrize("phone", ["(31) 99876-5432", "+55 31 99876-5432", "(11) 3333-4444"])
def test_phone(phone):
    assert ("phone", phone, "none") in labels(f"ligue {phone} hoje")


def test_invalid_phone_dropped():
    assert labels("ligue (20) 99876-5432") == []


def test_cep_needs_context():
    assert ("cep", "30130-100", "none") in labels("CEP 30130-100")
    assert labels("lote 30130-100") == []


def test_birth_date_with_context_and_valid_date():
    assert ("birth_date", "07/03/1985", "none") in labels("nascida em 07/03/1985")
    assert labels("nascida em 31/02/1985") == []
    assert labels("vencimento 07/03/1985") == []


def test_offsets_point_at_text():
    text = "Sr. X, CPF 123.456.789-09, ok"
    for e in rec.find(text):
        assert text[e.start : e.end] == e.text

import pytest

from privacyseed_lgpd.taxonomy import load_taxonomy, parse_taxonomy

LABELS = {
    "cpf", "cnpj", "pis", "cnh", "voter_id", "credit_card", "email", "phone", "cep",
    "person_name", "address", "birth_date", "sensitive_data",
}
SUBCATEGORIES = {
    "racial_ethnic_origin", "religious_belief", "political_opinion", "union_membership",
    "org_membership", "health", "sex_life", "genetic", "biometric",
}


def test_labels_and_subcategories():
    tax = load_taxonomy()
    assert set(tax.labels) == LABELS
    assert set(tax.subcategories) == SUBCATEGORIES


def test_default_actions():
    tax = load_taxonomy()
    assert tax.labels["cnpj"].default_action == "flag"
    assert all(i.default_action == "anonymize" for k, i in tax.labels.items() if k != "cnpj")


def test_tags_and_categories():
    tax = load_taxonomy()
    assert tax.tag("cpf") == "[CPF]"
    assert tax.tag("sensitive_data") == "[DADO_SENSIVEL]"
    assert tax.labels["sensitive_data"].lgpd_category == "art5_II"
    assert all(i.lgpd_category == "art5_I" for k, i in tax.labels.items() if k != "sensitive_data")


def test_notes():
    tax = load_taxonomy()
    assert "MEI" in tax.labels["cnpj"].note
    assert "não é dado sensível" in tax.labels["credit_card"].note


def test_maps_to_columns_exist():
    for info in load_taxonomy().labels.values():
        assert set(info.maps_to) == {"arthrod", "fastino", "presidio"}


def test_invalid_action_rejected():
    data = {
        "labels": {"x": {"name": "X", "tag": "X", "lgpd_category": "art5_I", "article": "a",
                         "description": "d", "default_action": "delete"}},
        "subcategories": {},
    }
    with pytest.raises(ValueError, match="default_action"):
        parse_taxonomy(data)

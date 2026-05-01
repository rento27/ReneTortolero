from decimal import Decimal
import pytest
from unittest.mock import patch, MagicMock
from notaria_4_core.backend.lib import fiscal_engine
from notaria_4_core.backend.lib.fiscal_engine import sanitize_name, validate_copropiedad, calculate_retentions, calculate_isai_manzanillo, validate_postal_code

def test_sanitize_name():
    input_name = "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V."
    expected = "INMOBILIARIA DEL PACIFICO"
    assert sanitize_name(input_name) == expected

    assert sanitize_name("Empresa Patito S.C.") == "EMPRESA PATITO"
    assert sanitize_name("  Espacios  Extra  ") == "ESPACIOS EXTRA"
    assert sanitize_name("Árbol") == "ARBOL"

def test_validate_copropiedad_success():
    percentages = [Decimal("50.00"), Decimal("50.00")]
    assert validate_copropiedad(percentages) is True

def test_validate_copropiedad_fail():
    percentages = [Decimal("33.33"), Decimal("33.33"), Decimal("33.33")]
    with pytest.raises(ValueError):
        validate_copropiedad(percentages)

def test_calculate_retentions_moral():
    rfc = "ABC123456T12"
    subtotal = Decimal("1000.00")
    ret = calculate_retentions(rfc, subtotal)

    assert ret["is_moral"] is True
    assert ret["isr"] == Decimal("100.00")
    assert ret["iva"] == Decimal("106.67")

def test_calculate_retentions_fisica():
    rfc = "ABCD123456T12"
    subtotal = Decimal("1000.00")
    ret = calculate_retentions(rfc, subtotal)

    assert ret["is_moral"] is False
    assert ret["isr"] == Decimal("0.00")

@patch("notaria_4_core.backend.lib.fiscal_engine.get_remote_config_sync")
def test_isai_manzanillo(mock_get_remote_config_sync):
    fiscal_engine._ISAI_RATE_CACHE = None
    mock_template = MagicMock()
    mock_template.parameters.get.return_value.default_value.value = "0.04"
    mock_get_remote_config_sync.return_value = mock_template

    price = Decimal("1000000.00")
    cadastral = Decimal("500000.00")
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("40000.00")

    fiscal_engine._ISAI_RATE_CACHE = None
    mock_get_remote_config_sync.side_effect = Exception("Firebase Error")
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("30000.00")

    assert calculate_isai_manzanillo(price, cadastral, Decimal("0.05")) == Decimal("50000.00")

def test_validate_postal_code():
    assert validate_postal_code("28200") is True
    assert validate_postal_code("28200", "COL") is True
    assert validate_postal_code("28200", "JAL") is False
    assert validate_postal_code("99999") is False

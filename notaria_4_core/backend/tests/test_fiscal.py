from decimal import Decimal
import pytest
from unittest.mock import patch, MagicMock
from notaria_4_core.backend.lib import fiscal_engine
from notaria_4_core.backend.lib.fiscal_engine import sanitize_name, validate_copropiedad, calculate_retentions, calculate_isai_manzanillo, validate_postal_code, validate_conceptos_objeto_imp

def test_sanitize_name():
    # Test removal of S.A. DE C.V.
    input_name = "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V."
    # Expect accents removed and regime removed
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
    # RFC 12 chars
    rfc = "ABC123456T12"
    subtotal = Decimal("1000.00")
    ret = calculate_retentions(rfc, subtotal)

    assert ret["is_moral"] is True
    assert ret["isr"] == Decimal("100.00") # 10%
    # IVA Ret = 1000 * 0.16 * 2/3 = 160 * 0.6666... = 106.666... -> 106.67
    assert ret["iva"] == Decimal("106.67")

def test_calculate_retentions_fisica():
    # RFC 13 chars
    rfc = "ABCD123456T12"
    subtotal = Decimal("1000.00")
    ret = calculate_retentions(rfc, subtotal)

    assert ret["is_moral"] is False
    assert ret["isr"] == Decimal("0.00")

@patch("notaria_4_core.backend.lib.fiscal_engine.get_remote_config_sync")
@patch("firebase_admin.get_app")
def test_isai_manzanillo(mock_get_app, mock_get_remote_config):
    fiscal_engine._ISAI_RATE_CACHE = None

    mock_template = MagicMock()
    mock_val = MagicMock()
    mock_val.default_value.value = "0.03"
    mock_template.parameters.get.return_value = mock_val
    mock_get_remote_config.return_value = mock_template

    price = Decimal("1000000.00")
    cadastral = Decimal("500000.00")
    # Max is 1M. Rate 0.03 -> 30,000
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("30000.00")

    # Cadastral higher
    assert calculate_isai_manzanillo(price, Decimal("2000000.00")) == Decimal("60000.00")

@patch("notaria_4_core.backend.lib.fiscal_engine.get_remote_config_sync")
@patch("firebase_admin.get_app")
def test_isai_manzanillo_remote_config(mock_get_app, mock_get_remote_config):
    fiscal_engine._ISAI_RATE_CACHE = None

    mock_template = MagicMock()
    mock_val = MagicMock()
    mock_val.default_value.value = "0.05"
    mock_template.parameters.get.return_value = mock_val
    mock_get_remote_config.return_value = mock_template

    price = Decimal("1000000.00")
    cadastral = Decimal("500000.00")
    # Max is 1M. Rate 0.05 -> 50,000
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("50000.00")

def test_validate_conceptos_objeto_imp():
    # Valid
    assert validate_conceptos_objeto_imp([
        {"descripcion": "Honorarios Notariales", "objeto_imp": "02"},
        {"descripcion": "Suplidos por Registro", "objeto_imp": "01"},
        {"descripcion": "Derechos Estatales", "objeto_imp": "01"}
    ]) is True

    # Invalid Honorarios
    with pytest.raises(ValueError, match="ObjetoImp '02'"):
        validate_conceptos_objeto_imp([
            {"descripcion": "Honorarios", "objeto_imp": "01"}
        ])

    # Invalid Suplidos
    with pytest.raises(ValueError, match="ObjetoImp '01'"):
        validate_conceptos_objeto_imp([
            {"descripcion": "Suplidos", "objeto_imp": "02"}
        ])

def test_validate_postal_code():
    # Known CP
    assert validate_postal_code("28200") is True
    assert validate_postal_code("28200", "COL") is True

    # Wrong State
    assert validate_postal_code("28200", "JAL") is False

    # Unknown CP
    assert validate_postal_code("99999") is False

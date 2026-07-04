from decimal import Decimal
import pytest
from unittest.mock import patch
from notaria_4_core.backend.lib.fiscal_engine import sanitize_name, validate_copropiedad, calculate_retentions, calculate_isai_manzanillo, validate_postal_code, validate_conceptos_objeto_imp
import notaria_4_core.backend.lib.fiscal_engine as fiscal_engine

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
def test_isai_manzanillo(mock_get_remote_config_sync):
    fiscal_engine._ISAI_RATE_CACHE = None

    class MockValue:
        def __init__(self, val):
            self.value = val

    class MockDefaultValue:
        def __init__(self, val):
            self.default_value = MockValue(val)

    class MockTemplate:
        def __init__(self):
            self.parameters = {"tasa_isai_manzanillo": MockDefaultValue("0.05")}

    mock_get_remote_config_sync.return_value = MockTemplate()

    price = Decimal("1000000.00")
    cadastral = Decimal("500000.00")
    # Max is 1M. Rate 0.05 -> 50,000
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("50000.00")

    # Cadastral higher
    assert calculate_isai_manzanillo(price, Decimal("2000000.00")) == Decimal("100000.00")

    # Test default fallback when mocked call fails
    fiscal_engine._ISAI_RATE_CACHE = None
    mock_get_remote_config_sync.side_effect = Exception("Failed")
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("30000.00")

def test_validate_conceptos_objeto_imp():
    # Valid cases
    valid_conceptos = [
        {"descripcion": "HONORARIOS NOTARIALES", "objeto_imp": "02"},
        {"descripcion": "GASTOS SUPLIDOS", "objeto_imp": "01"},
        {"descripcion": "DERECHOS DE REGISTRO", "objeto_imp": "01"},
        {"descripcion": "OTRO CONCEPTO", "objeto_imp": "02"}
    ]
    assert validate_conceptos_objeto_imp(valid_conceptos) is True

    # Invalid cases
    with pytest.raises(ValueError):
        validate_conceptos_objeto_imp([{"descripcion": "HONORARIOS", "objeto_imp": "01"}])

    with pytest.raises(ValueError):
        validate_conceptos_objeto_imp([{"descripcion": "SUPLIDOS", "objeto_imp": "02"}])

def test_validate_postal_code():
    # Known CP
    assert validate_postal_code("28200") is True
    assert validate_postal_code("28200", "COL") is True

    # Wrong State
    assert validate_postal_code("28200", "JAL") is False

    # Unknown CP
    assert validate_postal_code("99999") is False

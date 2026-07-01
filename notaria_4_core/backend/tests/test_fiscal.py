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
def test_isai_manzanillo(mock_get_rate):
    mock_get_rate.return_value = Decimal("0.03")
    fiscal_engine._ISAI_RATE_CACHE = None # clear cache

    price = Decimal("1000000.00")
    cadastral = Decimal("500000.00")
    # Max is 1M. Rate 0.03 -> 30,000
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("30000.00")

    # Cadastral higher
    assert calculate_isai_manzanillo(price, Decimal("2000000.00")) == Decimal("60000.00")

def make_firestore_postal_code_mock(exists, estado=None):
    mock_db = MagicMock()
    mock_doc = MagicMock()
    mock_doc.exists = exists
    mock_doc.to_dict.return_value = {"estado": estado} if estado else {}
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
    return mock_db

@patch('notaria_4_core.backend.lib.fiscal_engine.firestore', create=True)
def test_validate_postal_code(mock_firestore):
    # Known CP
    mock_firestore.client.return_value = make_firestore_postal_code_mock(True, "COL")
    assert validate_postal_code("28200") is True

    mock_firestore.client.return_value = make_firestore_postal_code_mock(True, "COL")
    assert validate_postal_code("28200", "COL") is True

    # Wrong State
    mock_firestore.client.return_value = make_firestore_postal_code_mock(True, "COL")
    assert validate_postal_code("28200", "JAL") is False

    # Unknown CP
    mock_firestore.client.return_value = make_firestore_postal_code_mock(False)
    assert validate_postal_code("99999") is False

def test_validate_conceptos_objeto_imp():
    valid_conceptos = [
        {"descripcion": "Honorarios por servicios", "objeto_imp": "02"},
        {"descripcion": "Pago de derechos", "objeto_imp": "01"}
    ]
    assert validate_conceptos_objeto_imp(valid_conceptos) is True

    invalid_honorarios = [{"descripcion": "Honorarios notariales", "objeto_imp": "01"}]
    with pytest.raises(ValueError, match="ObjetoImp '02'"):
        validate_conceptos_objeto_imp(invalid_honorarios)

    invalid_suplidos = [{"descripcion": "Gastos suplidos", "objeto_imp": "02"}]
    with pytest.raises(ValueError, match="ObjetoImp '01'"):
        validate_conceptos_objeto_imp(invalid_suplidos)

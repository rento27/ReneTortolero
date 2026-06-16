from decimal import Decimal
import pytest
from unittest.mock import patch, MagicMock
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
    # IVA Ret = 1000 * 0.106667 = 106.667 -> 106.67
    assert ret["iva"] == Decimal("106.67")

def test_calculate_retentions_fisica():
    # RFC 13 chars
    rfc = "ABCD123456T12"
    subtotal = Decimal("1000.00")
    ret = calculate_retentions(rfc, subtotal)

    assert ret["is_moral"] is False
    assert ret["isr"] == Decimal("0.00")

@patch("notaria_4_core.backend.lib.fiscal_engine.get_remote_config_sync")
def test_isai_manzanillo(mock_get_remote_config):
    # Setup state leak prevention
    fiscal_engine._ISAI_RATE_CACHE = None
    mock_get_remote_config.return_value = Decimal("0.03")

    price = Decimal("1000000.00")
    cadastral = Decimal("500000.00")
    # Max is 1M. Rate 0.03 -> 30,000
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("30000.00")

    # Cadastral higher
    assert calculate_isai_manzanillo(price, Decimal("2000000.00")) == Decimal("60000.00")

def make_firestore_postal_code_mock(expected_cp, expected_state=None, returns_data=True):
    mock_firestore = MagicMock()
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_where1 = MagicMock()
    mock_where2 = MagicMock()
    mock_limit = MagicMock()

    mock_firestore.client.return_value = mock_client
    mock_client.collection.return_value = mock_collection
    mock_collection.where.return_value = mock_where1
    mock_where1.where.return_value = mock_where2

    if returns_data:
        mock_limit.get.return_value = [MagicMock()]
    else:
        mock_limit.get.return_value = []

    mock_where1.limit.return_value = mock_limit
    mock_where2.limit.return_value = mock_limit

    return mock_firestore

@patch('firebase_admin.firestore', create=True)
def test_validate_postal_code(mock_firestore_patch):
    import notaria_4_core.backend.lib.fiscal_engine as fe

    # Known CP
    fe.firestore = make_firestore_postal_code_mock("28200")
    assert fe.validate_postal_code("28200") is True

    fe.firestore = make_firestore_postal_code_mock("28200", "COL")
    assert fe.validate_postal_code("28200", "COL") is True

    # Wrong State
    fe.firestore = make_firestore_postal_code_mock("28200", "JAL", returns_data=False)
    assert fe.validate_postal_code("28200", "JAL") is False

    # Unknown CP
    fe.firestore = make_firestore_postal_code_mock("99999", returns_data=False)
    assert fe.validate_postal_code("99999") is False

def test_validate_conceptos_objeto_imp():
    conceptos_valid = [
        {'descripcion': 'Honorarios por servicios notariales', 'objeto_imp': '02'},
        {'descripcion': 'Suplidos de viaje', 'objeto_imp': '01'}
    ]
    assert validate_conceptos_objeto_imp(conceptos_valid) is True

    conceptos_invalid_1 = [
        {'descripcion': 'Honorarios por servicios notariales', 'objeto_imp': '01'}
    ]
    with pytest.raises(ValueError):
        validate_conceptos_objeto_imp(conceptos_invalid_1)

    conceptos_invalid_2 = [
        {'descripcion': 'Derechos de registro', 'objeto_imp': '02'}
    ]
    with pytest.raises(ValueError):
        validate_conceptos_objeto_imp(conceptos_invalid_2)

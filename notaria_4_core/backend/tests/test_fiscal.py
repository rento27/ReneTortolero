import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock

# Important: ensure _ISAI_RATE_CACHE reset before import to have a clean slate if needed
import notaria_4_core.backend.lib.fiscal_engine as fiscal_engine
from notaria_4_core.backend.lib.fiscal_engine import (
    sanitize_name, validate_copropiedad, calculate_retentions,
    calculate_isai_manzanillo, validate_postal_code
)

def make_firestore_postal_code_mock(exists, expected_state=None):
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_document = MagicMock()
    mock_doc_snapshot = MagicMock()

    mock_db.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document
    mock_document.get.return_value = mock_doc_snapshot

    mock_doc_snapshot.exists = exists
    if exists and expected_state:
        mock_doc_snapshot.to_dict.return_value = {'estado': expected_state}
    else:
        mock_doc_snapshot.to_dict.return_value = {}

    return mock_db


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

@patch('notaria_4_core.backend.lib.fiscal_engine.get_remote_config_sync')
def test_isai_manzanillo(mock_get_remote_config_sync):
    fiscal_engine._ISAI_RATE_CACHE = None

    mock_template = MagicMock()
    mock_param = MagicMock()
    mock_param.default_value.value = "0.04"
    mock_template.parameters = {'tasa_isai_manzanillo': mock_param}
    mock_get_remote_config_sync.return_value = mock_template

    price = Decimal("1000000.00")
    cadastral = Decimal("500000.00")

    # 4% of 1,000,000 is 40,000
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("40000.00")
    mock_get_remote_config_sync.assert_called_once()

    # Test fallback to default when mock fails
    fiscal_engine._ISAI_RATE_CACHE = None
    mock_get_remote_config_sync.side_effect = Exception("Network Error")

    # 3% of 1,000,000 is 30,000
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("30000.00")

    # Test explicit rate
    fiscal_engine._ISAI_RATE_CACHE = None
    assert calculate_isai_manzanillo(price, cadastral, Decimal("0.05")) == Decimal("50000.00")


@patch('firebase_admin.firestore', create=True)
def test_validate_postal_code(mock_firestore):
    # Known CP
    mock_firestore.client.return_value = make_firestore_postal_code_mock(True)
    assert validate_postal_code("28200") is True

    # Known CP with correct state
    mock_firestore.client.return_value = make_firestore_postal_code_mock(True, "COL")
    assert validate_postal_code("28200", "COL") is True

    # Wrong State
    mock_firestore.client.return_value = make_firestore_postal_code_mock(True, "COL")
    assert validate_postal_code("28200", "JAL") is False

    # Unknown CP
    mock_firestore.client.return_value = make_firestore_postal_code_mock(False)
    assert validate_postal_code("99999") is False

from decimal import Decimal
import pytest
import sys
from unittest.mock import patch, MagicMock

# Patch firebase_admin.firestore system-wide
mock_firestore = MagicMock()
sys.modules['firebase_admin.firestore'] = mock_firestore

from notaria_4_core.backend.lib import fiscal_engine
from notaria_4_core.backend.lib.fiscal_engine import sanitize_name, validate_copropiedad, calculate_retentions, calculate_isai_manzanillo, validate_postal_code

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
def test_isai_manzanillo(mock_get_config):
    fiscal_engine._ISAI_RATE_CACHE = None
    mock_get_config.return_value = "0.03"

    price = Decimal("1000000.00")
    cadastral = Decimal("500000.00")
    # Max is 1M. Rate 0.03 -> 30,000
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("30000.00")

    # Cadastral higher
    assert calculate_isai_manzanillo(price, Decimal("2000000.00")) == Decimal("60000.00")

@patch('firebase_admin.initialize_app')
@patch('firebase_admin.get_app')
@patch('notaria_4_core.backend.lib.fiscal_engine.firestore')
def test_validate_postal_code(mock_firestore_local, mock_get_app, mock_init_app):
    mock_db = MagicMock()
    mock_firestore_local.client.return_value = mock_db

    # Setup mock for valid CP 28200 COL
    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = {"c_CodigoPostal": "28200", "c_Estado": "COL"}

    mock_query = mock_db.collection.return_value.where.return_value.limit.return_value.stream

    # Known CP
    mock_query.return_value = [mock_doc]
    assert validate_postal_code("28200") is True

    mock_query.return_value = [mock_doc]
    assert validate_postal_code("28200", "COL") is True

    # Wrong State
    mock_query.return_value = [mock_doc]
    assert validate_postal_code("28200", "JAL") is False

    # Unknown CP
    mock_query.return_value = []
    assert validate_postal_code("99999") is False

from decimal import Decimal
import pytest
from unittest.mock import patch, MagicMock
import sys

# Patch firebase_admin system-wide before importing fiscal_engine
sys.modules['firebase_admin.firestore'] = MagicMock()
mock_initialize_app = patch('firebase_admin.initialize_app').start()
mock_get_app = patch('firebase_admin.get_app').start()

import notaria_4_core.backend.lib.fiscal_engine as fiscal_engine
from notaria_4_core.backend.lib.fiscal_engine import sanitize_name, validate_copropiedad, calculate_retentions, calculate_isai_manzanillo, validate_postal_code

@pytest.fixture(autouse=True)
def clear_cache():
    # Clear cache before each test to prevent state leakage
    fiscal_engine._ISAI_RATE_CACHE = None
    fiscal_engine._ISAI_RATE_CACHE_TIME = 0

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
    # Mock template response
    mock_template = MagicMock()
    mock_template.parameters = {
        'tasa_isai_manzanillo': MagicMock(default_value=MagicMock(value="0.03"))
    }
    mock_get_remote_config_sync.return_value = mock_template

    price = Decimal("1000000.00")
    cadastral = Decimal("500000.00")
    # Max is 1M. Rate 0.03 -> 30,000
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("30000.00")

    # Cadastral higher
    assert calculate_isai_manzanillo(price, Decimal("2000000.00")) == Decimal("60000.00")

def test_validate_postal_code():
    # Because we mocked firestore system-wide, we should test the fallback or mocked behavior.
    # The current validation in fiscal_engine for firebase will attempt to use firestore.client().
    # Let's mock it to behave like the stub.
    db_mock = MagicMock()
    doc_ref_mock = MagicMock()
    doc_mock = MagicMock()
    doc_mock.exists = True
    doc_mock.to_dict.return_value = {'estado': 'COL'}
    doc_ref_mock.get.return_value = doc_mock
    db_mock.collection.return_value.document.return_value = doc_ref_mock
    fiscal_engine.firestore.client.return_value = db_mock

    # Known CP (mocked to always return True with 'COL' state)
    assert validate_postal_code("28200") is True
    assert validate_postal_code("28200", "COL") is True

    # Wrong State (mocked returns 'COL')
    assert validate_postal_code("28200", "JAL") is False

    # Unknown CP
    doc_mock_fail = MagicMock()
    doc_mock_fail.exists = False
    doc_ref_mock_fail = MagicMock()
    doc_ref_mock_fail.get.return_value = doc_mock_fail
    # Change mock for this specific call to return False
    with patch.object(db_mock.collection.return_value, 'document', return_value=doc_ref_mock_fail):
        assert validate_postal_code("99999") is False

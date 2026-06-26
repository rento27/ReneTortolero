import importlib
from decimal import Decimal
import pytest
from unittest.mock import patch, MagicMock

# We need to import the module to manipulate its globals
import notaria_4_core.backend.lib.fiscal_engine as fiscal_engine_module
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

@patch('notaria_4_core.backend.lib.fiscal_engine.get_remote_config_sync')
def test_isai_manzanillo_remote_config(mock_get_remote_config_sync):
    # Clear the cache before running the test to ensure no state leakage
    fiscal_engine_module._ISAI_RATE_CACHE = None
    fiscal_engine_module._ISAI_RATE_LAST_FETCH = None

    # Mock the returned parameter
    class MockParam:
        class MockValue:
            value = "0.05"
        default_value = MockValue()

    mock_get_remote_config_sync.return_value = {
        'tasa_isai_manzanillo': MockParam()
    }

    price = Decimal("1000000.00")
    cadastral = Decimal("500000.00")
    # Max is 1M. Mocked Rate 0.05 -> 50,000
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("50000.00")
    mock_get_remote_config_sync.assert_called_once()

    # Clear cache again for subsequent tests if any
    fiscal_engine_module._ISAI_RATE_CACHE = None
    fiscal_engine_module._ISAI_RATE_LAST_FETCH = None

@patch('notaria_4_core.backend.lib.fiscal_engine.get_remote_config_sync')
def test_isai_manzanillo_fallback(mock_get_remote_config_sync):
    fiscal_engine_module._ISAI_RATE_CACHE = None
    fiscal_engine_module._ISAI_RATE_LAST_FETCH = None

    # Simulate empty remote config
    mock_get_remote_config_sync.return_value = {}

    price = Decimal("1000000.00")
    cadastral = Decimal("500000.00")
    # Fallback rate is 0.03 -> 30,000
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("30000.00")

    fiscal_engine_module._ISAI_RATE_CACHE = None
    fiscal_engine_module._ISAI_RATE_LAST_FETCH = None

def make_firestore_postal_code_mock(exists=True, estado="COL"):
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_document = MagicMock()
    mock_doc_snapshot = MagicMock()

    mock_doc_snapshot.exists = exists
    mock_doc_snapshot.to_dict.return_value = {'estado': estado} if exists else None

    mock_document.get.return_value = mock_doc_snapshot
    mock_collection.document.return_value = mock_document
    mock_db.collection.return_value = mock_collection

    mock_firestore = MagicMock()
    mock_firestore.client.return_value = mock_db
    return mock_firestore

@patch('notaria_4_core.backend.lib.fiscal_engine.firestore', create=True)
def test_validate_postal_code_success(mock_firestore):
    mock_firestore.client = make_firestore_postal_code_mock(exists=True, estado="COL").client

    assert validate_postal_code("28200") is True
    assert validate_postal_code("28200", "COL") is True

@patch('notaria_4_core.backend.lib.fiscal_engine.firestore', create=True)
def test_validate_postal_code_wrong_state(mock_firestore):
    mock_firestore.client = make_firestore_postal_code_mock(exists=True, estado="COL").client

    # Exists, but we expect JAL, while it returns COL
    assert validate_postal_code("28200", "JAL") is False

@patch('notaria_4_core.backend.lib.fiscal_engine.firestore', create=True)
def test_validate_postal_code_not_found(mock_firestore):
    mock_firestore.client = make_firestore_postal_code_mock(exists=False).client

    # Unknown CP
    assert validate_postal_code("99999") is False

def test_validate_conceptos_objeto_imp():
    # Valid concepts
    valid_conceptos = [
        {"Descripcion": "Honorarios notariales", "ObjetoImp": "02"},
        {"Descripcion": "Suplidos y gastos", "ObjetoImp": "01"},
        {"Descripcion": "Derechos de registro", "ObjetoImp": "01"},
    ]
    assert validate_conceptos_objeto_imp(valid_conceptos) is True

    # Invalid Honorarios
    with pytest.raises(ValueError, match="Honorarios must have ObjetoImp '02'."):
        validate_conceptos_objeto_imp([{"Descripcion": "Honorarios por servicios", "ObjetoImp": "01"}])

    # Invalid Suplidos
    with pytest.raises(ValueError, match="Suplidos and Derechos must have ObjetoImp '01'."):
        validate_conceptos_objeto_imp([{"Descripcion": "Suplidos", "ObjetoImp": "02"}])

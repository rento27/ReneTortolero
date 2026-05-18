from decimal import Decimal
import pytest
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

from unittest.mock import patch, MagicMock
from notaria_4_core.backend.lib import fiscal_engine

def test_isai_manzanillo():
    # Clear cache before test
    fiscal_engine._ISAI_RATE_CACHE = None

    price = Decimal("1000000.00")
    cadastral = Decimal("500000.00")

    with patch("notaria_4_core.backend.lib.fiscal_engine.get_remote_config_sync") as mock_get_rc:
        # Mocking the remote config template
        mock_template = MagicMock()
        mock_param = MagicMock()
        mock_param.default_value.value = "0.04"
        mock_template.parameters = {"tasa_isai_manzanillo": mock_param}
        mock_get_rc.return_value = mock_template

        # Max is 1M. Rate 0.04 -> 40,000
        assert calculate_isai_manzanillo(price, cadastral) == Decimal("40000.00")

        # Test cache logic
        mock_get_rc.reset_mock()
        assert calculate_isai_manzanillo(price, cadastral) == Decimal("40000.00")
        mock_get_rc.assert_not_called()

        # Cadastral higher
        assert calculate_isai_manzanillo(price, Decimal("2000000.00")) == Decimal("80000.00")

def test_validate_postal_code():
    # Mock firebase setup
    with patch("notaria_4_core.backend.lib.fiscal_engine.firebase_admin", MagicMock()):

        # We need to mock the firestore import that happens locally within the validate function
        with patch.dict('sys.modules', {'firebase_admin.firestore': MagicMock()}) as mock_firestore_mod:
            # We can retrieve the mocked module to set up our assertions
            import sys
            mock_firestore = sys.modules['firebase_admin.firestore']

            mock_db = MagicMock()
            mock_firestore.client.return_value = mock_db
            mock_query = MagicMock()
            mock_db.collection.return_value.where.return_value.limit.return_value = mock_query

            # Found CP
            mock_doc = MagicMock()
            mock_doc.to_dict.return_value = {"c_CodigoPostal": "28200", "c_Estado": "COL"}
            mock_query.stream.return_value = [mock_doc]

            assert validate_postal_code("28200") is True
            assert validate_postal_code("28200", "COL") is True
            assert validate_postal_code("28200", "JAL") is False

            # Unknown CP
            mock_query.stream.return_value = []
            assert validate_postal_code("99999") is False

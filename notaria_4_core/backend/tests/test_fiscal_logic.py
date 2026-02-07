from decimal import Decimal
import pytest
import sys
import os

# Add the backend directory to sys.path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.lib.fiscal_engine import sanitize_name, calculate_retentions, validate_copropiedad, validate_postal_code, calculate_isai_manzanillo

def test_sanitize_name():
    # Test 1: Standard case with "S.A. DE C.V."
    assert sanitize_name("INMOBILIARIA DEL PACÍFICO, S.A. DE C.V.") == "INMOBILIARIA DEL PACIFICO"

    # Test 2: With "S.C."
    assert sanitize_name("CONSULTORES JURIDICOS, S.C.") == "CONSULTORES JURIDICOS"

    # Test 3: With accents and extra spaces
    assert sanitize_name("  Constructora  San José,   S.A. de C.V.  ") == "CONSTRUCTORA SAN JOSE"

    # Test 4: No regime
    assert sanitize_name("JUAN PEREZ LOPEZ") == "JUAN PEREZ LOPEZ"

    # Test 5: S.A.P.I. DE C.V.
    assert sanitize_name("EMPRESA INNOVADORA, S.A.P.I. DE C.V.") == "EMPRESA INNOVADORA"

def test_calculate_retentions():
    # Test 1: Persona Moral (12 chars)
    rfc_moral = "ABC123456T1A" # 12 chars
    subtotal = Decimal("1000.00")
    ret = calculate_retentions(rfc_moral, subtotal)

    assert ret['is_moral'] is True
    assert ret['isr'] == Decimal("100.00") # 10%
    # IVA Retention: 1000 * 0.16 * (2/3) = 160 * 0.66666... = 106.666... -> 106.67
    assert ret['iva'] == Decimal("106.67")

    # Test 2: Persona Fisica (13 chars)
    rfc_fisica = "ABCD123456T1A" # 13 chars
    ret_fisica = calculate_retentions(rfc_fisica, subtotal)
    assert ret_fisica['is_moral'] is False
    assert ret_fisica['isr'] == Decimal("0.00")
    assert ret_fisica['iva'] == Decimal("0.00")

def test_validate_copropiedad():
    # Test 1: Exact 100%
    percentages = [Decimal("50.00"), Decimal("50.00")]
    assert validate_copropiedad(percentages) is True

    # Test 2: 99.99% (Should fail)
    percentages_bad = [Decimal("33.33"), Decimal("33.33"), Decimal("33.33")]
    with pytest.raises(ValueError):
        validate_copropiedad(percentages_bad)

    # Test 3: 100.01% (Should fail)
    percentages_over = [Decimal("50.00"), Decimal("50.01")]
    with pytest.raises(ValueError):
        validate_copropiedad(percentages_over)

def test_validate_postal_code():
    assert validate_postal_code("28200", "COL") is True
    assert validate_postal_code("06600", "CMX") is True
    assert validate_postal_code("00000") is False # Not in stub

def test_calculate_isai_manzanillo():
    price = Decimal("1000000.00")
    cadastral = Decimal("800000.00")
    # Max is 1,000,000. Rate is 0.03. ISAI = 30,000.00
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("30000.00")

    # Cadastral higher
    price = Decimal("500000.00")
    cadastral = Decimal("600000.00")
    # Max is 600,000. ISAI = 18,000.00
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("18000.00")

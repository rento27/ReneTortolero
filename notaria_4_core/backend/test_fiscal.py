import pytest
from decimal import Decimal
from lib.fiscal_engine import sanitize_name, calculate_retentions, calculate_isai, validate_copropiedad

def test_sanitize_name():
    # Test cases for corporate suffixes
    assert sanitize_name("INMOBILIARIA DEL PACÍFICO, S.A. DE C.V.") == "INMOBILIARIA DEL PACÍFICO"
    assert sanitize_name("GRUPO CONSTRUCTOR S.A.") == "GRUPO CONSTRUCTOR"
    assert sanitize_name("CONSULTORES S.C.") == "CONSULTORES"
    assert sanitize_name("AGI BUILDING SYNERGY") == "AGI BUILDING SYNERGY" # No suffix
    assert sanitize_name("EMPRESA SAS") == "EMPRESA"

def test_retentions_persona_moral():
    # RFC length 12 triggers retention
    pm_rfc = "TOSR520601AZ" # 12 chars
    subtotal = Decimal("1000.00")

    ret = calculate_retentions(subtotal, pm_rfc)

    # ISR 10%
    assert ret["isr_retention"] == Decimal("100.00")

    # IVA Retention: (1000 * 0.16) * (2/3) = 160 * 0.6666... = 106.666... -> 106.67
    assert ret["iva_retention"] == Decimal("106.67")

def test_retentions_persona_fisica():
    # RFC length 13 - No retention
    pf_rfc = "TOSR520601AZ4" # 13 chars
    subtotal = Decimal("1000.00")

    ret = calculate_retentions(subtotal, pf_rfc)
    assert ret["isr_retention"] == Decimal("0.00")
    assert ret["iva_retention"] == Decimal("0.00")

def test_isai_manzanillo():
    # Max(Price, Cadastral) * Rate
    price = Decimal("1000000.00")
    cadastral = Decimal("800000.00")
    rate = Decimal("0.03")

    # Base is Price
    assert calculate_isai(price, cadastral, rate) == Decimal("30000.00")

    # Base is Cadastral
    cadastral_high = Decimal("1500000.00")
    assert calculate_isai(price, cadastral_high, rate) == Decimal("45000.00")

def test_validate_copropiedad():
    valid = [Decimal("50.00"), Decimal("50.00")]
    assert validate_copropiedad(valid) is True

    invalid_low = [Decimal("33.33"), Decimal("33.33"), Decimal("33.33")] # 99.99
    assert validate_copropiedad(invalid_low) is False

    invalid_high = [Decimal("50.00"), Decimal("50.01")] # 100.01
    assert validate_copropiedad(invalid_high) is False

import pytest
from decimal import Decimal
from lib.fiscal_engine import sanitize_name, calculate_isai_manzanillo, get_retention_rates, validate_copropiedad

def test_sanitize_name():
    # Standard removal
    assert sanitize_name("INMOBILIARIA DEL PACÍFICO, S.A. DE C.V.") == "INMOBILIARIA DEL PACÍFICO"
    # No regime
    assert sanitize_name("AGI BUILDING SYNERGY") == "AGI BUILDING SYNERGY"
    # Different regime
    assert sanitize_name("EMPRESA, S.C.") == "EMPRESA"
    # Spacing cleanup
    assert sanitize_name(" GRUPO   INDUSTRIAL ") == "GRUPO INDUSTRIAL"
    # Regime without comma
    assert sanitize_name("EMPRESA S.A. DE C.V.") == "EMPRESA"
    # S.A.B
    assert sanitize_name("BANCO S.A.B. DE C.V.") == "BANCO"

def test_calculate_isai_manzanillo():
    # Price > Cadastral
    assert calculate_isai_manzanillo(Decimal("100000.00"), Decimal("50000.00")) == Decimal("3000.00") # 3% of 100k
    # Cadastral > Price
    assert calculate_isai_manzanillo(Decimal("50000.00"), Decimal("100000.00")) == Decimal("3000.00")
    # Rounding
    # 33.33 * 0.03 = 0.9999 -> 1.00
    assert calculate_isai_manzanillo(Decimal("33.33"), Decimal("0"), Decimal("0.03")) == Decimal("1.00")

def test_get_retention_rates():
    # Persona Moral (12 chars)
    rfc_moral = "ABC123456789"
    rates = get_retention_rates(rfc_moral)
    assert rates["isr"] == Decimal("0.10")
    assert rates["iva"] == Decimal("0.106667")

    # Persona Fisica (13 chars)
    rfc_fisica = "ABCD123456789"
    rates_fisica = get_retention_rates(rfc_fisica)
    assert rates_fisica["isr"] == Decimal("0.00")
    assert rates_fisica["iva"] == Decimal("0.00")

def test_validate_copropiedad():
    assert validate_copropiedad([Decimal("50.00"), Decimal("50.00")]) is True
    assert validate_copropiedad([Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]) is True
    assert validate_copropiedad([Decimal("50.00"), Decimal("49.99")]) is False

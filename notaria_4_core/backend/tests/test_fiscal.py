from decimal import Decimal
from ..lib.fiscal_engine import sanitize_name, calculate_isai, calculate_retentions, validate_copropiedad, validate_rfc

def test_sanitize_name():
    assert sanitize_name("Inmobiliaria del Pacífico, S.A. de C.V.") == "INMOBILIARIA DEL PACIFICO"
    assert sanitize_name("Grupo Constructor, S.C.") == "GRUPO CONSTRUCTOR"
    assert sanitize_name("  Consultores  S.A. ") == "CONSULTORES"
    assert sanitize_name("Juan Perez") == "JUAN PEREZ"
    assert sanitize_name("Empresa S.A. de C.V.,") == "EMPRESA" # Trailing comma check

def test_calculate_isai():
    # Manzanillo ISAI: Max(Price, Catastral) * Rate
    price = Decimal("1000000.00")
    catastral = Decimal("800000.00")
    rate = Decimal("0.03") # 3%

    # Expected: 1,000,000 * 0.03 = 30,000.00
    assert calculate_isai(price, catastral, rate) == Decimal("30000.00")

    # Case where Catastral is higher
    catastral_high = Decimal("1200000.00")
    # Expected: 1,200,000 * 0.03 = 36,000.00
    assert calculate_isai(price, catastral_high, rate) == Decimal("36000.00")

def test_calculate_retentions_persona_moral():
    rfc_moral = "ABC123456T12" # 12 chars
    subtotal = Decimal("10000.00")
    iva = Decimal("1600.00")

    rets = calculate_retentions(rfc_moral, subtotal, iva)

    # ISR 10% of 10,000 = 1,000.00
    assert rets['ret_isr'] == Decimal("1000.00")

    # IVA 2/3 of 1,600 = 1066.67
    # 1600 * 2 / 3 = 1066.6666... -> 1066.67
    assert rets['ret_iva'] == Decimal("1066.67")

def test_calculate_retentions_persona_fisica():
    rfc_fisica = "ABCD123456T12" # 13 chars
    subtotal = Decimal("10000.00")
    iva = Decimal("1600.00")

    rets = calculate_retentions(rfc_fisica, subtotal, iva)
    assert rets == {}

def test_validate_copropiedad():
    valid = [Decimal("50.00"), Decimal("50.00")]
    assert validate_copropiedad(valid) is True

    invalid = [Decimal("33.33"), Decimal("33.33"), Decimal("33.33")] # Sum 99.99
    assert validate_copropiedad(invalid) is False

    exact = [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")] # Sum 100.00
    assert validate_copropiedad(exact) is True

def test_validate_rfc():
    assert validate_rfc("XAXX010101000") is True # Generic
    assert validate_rfc("TOSR520601AZ4") is True
    assert validate_rfc("INVALID") is False

def test_get_retention_rates():
    from ..lib.fiscal_engine import get_retention_rates
    rates = get_retention_rates("ABC123456T12")
    assert rates['isr'] == Decimal("0.100000")
    assert rates['iva'] == Decimal("0.106667")

    rates_fisica = get_retention_rates("ABCD123456T12")
    assert rates_fisica == {}

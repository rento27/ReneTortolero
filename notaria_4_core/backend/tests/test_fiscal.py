import pytest
from decimal import Decimal
from lib.fiscal_engine import calculate_isai_manzanillo, calculate_retentions, validate_copropiedad, validate_postal_code, sanitize_name

def test_sanitize_name():
    assert sanitize_name("Inmobiliaria del Pacífico, S.A. de C.V.") == "INMOBILIARIA DEL PACIFICO"
    assert sanitize_name("  Consultoría  Integral S.C. ") == "CONSULTORIA INTEGRAL"
    assert sanitize_name("Juan Pérez") == "JUAN PEREZ"

def test_validate_postal_code():
    assert validate_postal_code("28200", "COL") is True
    assert validate_postal_code("06600", "CMX") is True
    assert validate_postal_code("99999") is False # Not in stub
    assert validate_postal_code("28200", "CMX") is False # Wrong state

def test_calculate_isai_manzanillo():
    # Scenario: Price > Cadastral
    price = Decimal("1000000.00")
    cadastral = Decimal("800000.00")
    rate = Decimal("0.03")
    expected = Decimal("30000.00") # 1,000,000 * 0.03
    assert calculate_isai_manzanillo(price, cadastral, rate) == expected

    # Scenario: Cadastral > Price
    price = Decimal("500000.00")
    cadastral = Decimal("600000.00")
    expected = Decimal("18000.00") # 600,000 * 0.03
    assert calculate_isai_manzanillo(price, cadastral, rate) == expected

def test_calculate_retentions_persona_moral():
    rfc_moral = "ABC123456789" # 12 chars
    subtotal = Decimal("1000.00")

    ret = calculate_retentions(rfc_moral, subtotal)
    assert ret['is_moral'] is True
    assert ret['isr'] == Decimal("100.00") # 10%

    # IVA Retention: 1000 * 0.106667 = 106.667 -> 106.67
    assert ret['iva'] == Decimal("106.67")

def test_calculate_retentions_persona_fisica():
    rfc_fisica = "ABCD123456789" # 13 chars
    subtotal = Decimal("1000.00")

    ret = calculate_retentions(rfc_fisica, subtotal)
    assert ret['is_moral'] is False
    assert ret['isr'] == Decimal("0.00")
    assert ret['iva'] == Decimal("0.00")

def test_validate_copropiedad():
    valid = [Decimal("50.00"), Decimal("50.00")]
    assert validate_copropiedad(valid) is True

    invalid_under = [Decimal("33.33"), Decimal("33.33"), Decimal("33.33")] # 99.99
    with pytest.raises(ValueError):
        validate_copropiedad(invalid_under)

    invalid_over = [Decimal("50.00"), Decimal("50.01")] # 100.01
    with pytest.raises(ValueError):
        validate_copropiedad(invalid_over)

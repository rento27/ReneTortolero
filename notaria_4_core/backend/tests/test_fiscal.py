from decimal import Decimal
import pytest
from lib.fiscal_engine import calculate_retentions, sanitize_name, IVA_RETENTION_RATE_DIRECT, calculate_isai_manzanillo, validate_postal_code

def test_retentions_persona_moral():
    # RFC 12 chars
    rfc = "ABC123456789"
    subtotal = Decimal("1000.00")

    ret = calculate_retentions(rfc, subtotal)

    assert ret['is_moral'] is True
    # ISR = 1000 * 0.10 = 100.00
    assert ret['isr'] == Decimal("100.00")
    # IVA = 1000 * 0.106667 = 106.67 (rounded)
    expected_iva = (subtotal * IVA_RETENTION_RATE_DIRECT).quantize(Decimal("0.01"))
    assert ret['iva'] == expected_iva
    assert ret['iva'] == Decimal("106.67")

def test_retentions_persona_fisica():
    # RFC 13 chars
    rfc = "ABCD123456789"
    subtotal = Decimal("1000.00")

    ret = calculate_retentions(rfc, subtotal)

    assert ret['is_moral'] is False
    assert ret['isr'] == Decimal("0.00")
    assert ret['iva'] == Decimal("0.00")

def test_sanitize_name():
    assert sanitize_name("INMOBILIARIA DEL PACÍFICO, S.A. DE C.V.") == "INMOBILIARIA DEL PACIFICO"
    assert sanitize_name("EMPRESA S.C.") == "EMPRESA"
    assert sanitize_name("JUAN PEREZ") == "JUAN PEREZ"
    assert sanitize_name("  ESPACIOS  ") == "ESPACIOS"

def test_isai_manzanillo():
    price = Decimal("1000000.00")
    cadastral = Decimal("900000.00")
    # Base = 1,000,000
    # Rate = 0.03
    # ISAI = 30,000.00
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("30000.00")

    price2 = Decimal("500000.00")
    cadastral2 = Decimal("600000.00")
    # Base = 600,000
    # ISAI = 18,000.00
    assert calculate_isai_manzanillo(price2, cadastral2) == Decimal("18000.00")

def test_validate_postal_code():
    assert validate_postal_code("28200") is True
    assert validate_postal_code("28200", "COL") is True
    assert validate_postal_code("28200", "CMX") is False
    assert validate_postal_code("00000") is False
    assert validate_postal_code("06600", "CMX") is True

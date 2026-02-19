import pytest
from decimal import Decimal
from lib.fiscal_engine import sanitize_name, calculate_retentions, IVA_RETENTION_RATE_DIRECT

def test_sanitize_name():
    # User example
    raw = "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V."
    expected = "INMOBILIARIA DEL PACIFICO"
    assert sanitize_name(raw) == expected

    # Other common forms
    raw2 = " GRUPO CONSTRUCTOR , S.C. "
    expected2 = "GRUPO CONSTRUCTOR"
    assert sanitize_name(raw2) == expected2

    # Verify simple name
    assert sanitize_name("Juan Perez") == "JUAN PEREZ"

def test_calculate_retentions_moral():
    # RFC 12 chars = Persona Moral
    rfc = "AAA010101AAA"
    subtotal = Decimal("1000.00")

    ret = calculate_retentions(rfc, subtotal)

    assert ret['is_moral'] is True
    # ISR 10%
    assert ret['isr'] == Decimal("100.00")
    # IVA Direct Rate 0.106667 * 1000 = 106.667 -> round 106.67
    assert ret['iva'] == Decimal("106.67")

def test_calculate_retentions_fisica():
    # RFC 13 chars = Persona Fisica
    rfc = "AAAA010101AAA"
    subtotal = Decimal("1000.00")

    ret = calculate_retentions(rfc, subtotal)

    assert ret['is_moral'] is False
    assert ret['isr'] == Decimal("0.00")
    assert ret['iva'] == Decimal("0.00")

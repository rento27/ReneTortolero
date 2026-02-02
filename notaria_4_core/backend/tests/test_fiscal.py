from decimal import Decimal
import pytest
from backend.lib.fiscal_engine import sanitize_name, calculate_retentions, calculate_isai, validate_copropiedad

def test_sanitize_name():
    # We preserve accents as SAT requires exact match with Constancia
    assert sanitize_name("INMOBILIARIA DEL PACÍFICO, S.A. DE C.V.") == "INMOBILIARIA DEL PACÍFICO"
    assert sanitize_name("CONSULTORES S.C.") == "CONSULTORES"
    assert sanitize_name("GRUPO INDUSTRIAL S. DE R.L. DE C.V.") == "GRUPO INDUSTRIAL"
    assert sanitize_name(" JUAN PEREZ ") == "JUAN PEREZ"
    assert sanitize_name("AGI BUILDING SYNERGY, S.A. DE C.V.") == "AGI BUILDING SYNERGY"

def test_calculate_retentions_moral():
    # RFC 12 chars
    subtotal = Decimal("1000.00")
    rfc = "AAA010101AAA" # 12 chars
    retentions = calculate_retentions(subtotal, rfc)

    # ISR 10%
    assert retentions["ISR"] == Decimal("100.00")

    # IVA 10.6667% (approx) -> 160 * 2 / 3
    expected_iva = (Decimal("1000.00") * Decimal("0.16") * Decimal("2") / Decimal("3"))
    # Check within small tolerance or exact if Decimal handles it
    assert retentions["IVA"] == expected_iva

def test_calculate_retentions_fisica():
    # RFC 13 chars
    subtotal = Decimal("1000.00")
    rfc = "AAAA010101AAA" # 13 chars
    retentions = calculate_retentions(subtotal, rfc)

    assert retentions["ISR"] == Decimal("0.00")
    assert retentions["IVA"] == Decimal("0.00")

def test_calculate_isai():
    # Max(1M, 500k) * 0.03 = 30k
    assert calculate_isai(Decimal("1000000"), Decimal("500000")) == Decimal("30000.00")
    # Max(500k, 1M) * 0.03 = 30k
    assert calculate_isai(Decimal("500000"), Decimal("1000000")) == Decimal("30000.00")

def test_validate_copropiedad():
    assert validate_copropiedad([Decimal("50.00"), Decimal("50.00")]) is True
    assert validate_copropiedad([Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]) is True
    assert validate_copropiedad([Decimal("33.33"), Decimal("33.33"), Decimal("33.33")]) is False

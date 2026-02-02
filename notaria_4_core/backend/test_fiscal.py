import pytest
from decimal import Decimal
from lib.fiscal_engine import sanitize_name, calculate_isai, calculate_retentions_persona_moral, validate_copropiedad

def test_sanitize_name():
    assert sanitize_name("Inmobiliaria Del Pacífico, S.A. de C.V.") == "INMOBILIARIA DEL PACIFICO"
    assert sanitize_name("  Empresa X S.C.  ") == "EMPRESA X"
    assert sanitize_name("Juan Perez") == "JUAN PEREZ"
    # Ensure it handles internal acronyms correctly if not at end (basic check)
    assert sanitize_name("Grupo S.A. de C.V. Construcciones") == "GRUPO S.A. DE C.V. CONSTRUCCIONES" # Regex anchors to end $

def test_calculate_isai_manzanillo():
    # Scenario 1: Operation Price is higher
    op_price = Decimal("1000000.00")
    cat_val = Decimal("800000.00")
    # Rate 3%
    expected = Decimal("30000.00")
    assert calculate_isai(op_price, cat_val) == expected

    # Scenario 2: Catastral Value is higher
    op_price = Decimal("500000.00")
    cat_val = Decimal("600000.00")
    expected = Decimal("18000.00") # 600k * 0.03
    assert calculate_isai(op_price, cat_val) == expected

def test_calculate_retentions_persona_moral():
    # Persona Fisica (RFC 13 chars) -> No retention
    assert calculate_retentions_persona_moral(Decimal("1000.00"), "XAXX010101000") == {}

    # Persona Moral (RFC 12 chars) -> Retention
    subtotal = Decimal("6083.91")
    retentions = calculate_retentions_persona_moral(subtotal, "ABC123456789")

    # ISR 10%
    expected_isr = Decimal("608.39")
    assert retentions['ret_isr'] == expected_isr

    # IVA 10.6667% (Two thirds of 16%)
    # Calculation: 6083.91 * 0.106666...
    # Let's check the math: 6083.91 * (2/3 * 0.16) = 6083.91 * 0.10666666 = 648.9504... -> 648.95
    expected_iva = Decimal("648.95")
    assert retentions['ret_iva'] == expected_iva

def test_validate_copropiedad():
    assert validate_copropiedad([Decimal("50.00"), Decimal("50.00")]) is True
    assert validate_copropiedad([Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]) is True
    assert validate_copropiedad([Decimal("99.99")]) is False

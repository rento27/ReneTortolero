import pytest
from decimal import Decimal
from lib.fiscal_engine import (
    sanitize_name,
    calculate_retentions_persona_moral,
    calculate_isai_manzanillo,
    validate_copropiedad
)

def test_sanitize_name():
    assert sanitize_name("Inmobiliaria Del Pacifico S.A. DE C.V.") == "INMOBILIARIA DEL PACIFICO"
    assert sanitize_name("  Consultores  S.C.  ") == "CONSULTORES"
    assert sanitize_name("Empresa Ficticia, S.A.") == "EMPRESA FICTICIA"
    assert sanitize_name("Juan Perez.") == "JUAN PEREZ"
    assert sanitize_name("Grupo Constructor S. de R.L. de C.V.") == "GRUPO CONSTRUCTOR"

def test_retentions_persona_moral():
    # Subtotal 1000. IVA 16% = 160.
    subtotal = Decimal("1000.00")
    rfc_moral = "ABC123456789" # 12 chars

    retentions = calculate_retentions_persona_moral(subtotal, rfc_moral)

    assert retentions is not None
    # ISR 10%
    assert retentions['isr_retention'] == Decimal("100.00")
    # IVA 2/3 of 160 = 106.6666... -> 106.67
    assert retentions['iva_retention'] == Decimal("106.67")

def test_retentions_persona_fisica():
    # 13 chars
    rfc_fisica = "ABCD123456789"
    retentions = calculate_retentions_persona_moral(Decimal("1000"), rfc_fisica)
    assert retentions is None

def test_isai_manzanillo():
    # Case 1: Price > Cadastral
    price = Decimal("1000000")
    cadastral = Decimal("800000")
    # Base 1,000,000 * 0.03 = 30,000
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("30000.00")

    # Case 2: Cadastral > Price
    price = Decimal("500000")
    cadastral = Decimal("600000")
    # Base 600,000 * 0.03 = 18,000
    assert calculate_isai_manzanillo(price, cadastral) == Decimal("18000.00")

def test_copropiedad_validation():
    assert validate_copropiedad([Decimal("50.00"), Decimal("50.00")]) is True
    assert validate_copropiedad([Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]) is True
    assert validate_copropiedad([Decimal("33.33"), Decimal("33.33"), Decimal("33.33")]) is False

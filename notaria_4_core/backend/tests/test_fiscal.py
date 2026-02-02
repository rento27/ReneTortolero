from decimal import Decimal
import pytest
from notaria_4_core.backend.lib.fiscal_engine import (
    calculate_isai_manzanillo,
    get_retention_rates,
    validate_copropiedad,
    sanitize_name
)

def test_calculate_isai_manzanillo():
    # Scenario: Price > Cadastral
    price = Decimal('1000000.00')
    cadastral = Decimal('800000.00')
    # 1,000,000 * 0.03 = 30,000.00
    assert calculate_isai_manzanillo(price, cadastral) == Decimal('30000.00')

    # Scenario: Cadastral > Price
    price = Decimal('500000.00')
    cadastral = Decimal('600000.00')
    # 600,000 * 0.03 = 18,000.00
    assert calculate_isai_manzanillo(price, cadastral) == Decimal('18000.00')

def test_retention_rates_persona_moral():
    rfc = "AAA010101AAA" # 12 chars
    rates = get_retention_rates(rfc)
    assert rates['isr_rate'] == Decimal('0.10')
    # Check iva_rate approx (since it's infinite decimal)
    # 0.16 * 2/3 = 0.1066666666...
    assert rates['iva_rate'] > Decimal('0.1066')
    assert rates['iva_rate'] < Decimal('0.1067')

def test_retention_rates_persona_fisica():
    rfc = "AAAA010101AAA" # 13 chars
    rates = get_retention_rates(rfc)
    assert rates['isr_rate'] == Decimal('0.00')
    assert rates['iva_rate'] == Decimal('0.00')

def test_validate_copropiedad():
    valid = [Decimal('50.00'), Decimal('50.00')]
    assert validate_copropiedad(valid) is True

    invalid_low = [Decimal('33.33'), Decimal('33.33'), Decimal('33.33')] # 99.99
    assert validate_copropiedad(invalid_low) is False

    invalid_high = [Decimal('50.00'), Decimal('50.01')]
    assert validate_copropiedad(invalid_high) is False

def test_sanitize_name():
    assert sanitize_name("Inmobiliaria del Pacífico, S.A. de C.V.") == "INMOBILIARIA DEL PACIFICO"
    assert sanitize_name("Grupo Constructor, S.C.") == "GRUPO CONSTRUCTOR"
    assert sanitize_name("Juan Perez.") == "JUAN PEREZ"
    assert sanitize_name("  Empresa   con   Espacios  ") == "EMPRESA CON ESPACIOS"
    # Test strict punctuation removal
    assert sanitize_name("Empresa, S.A.") == "EMPRESA"

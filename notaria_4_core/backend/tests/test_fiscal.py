from decimal import Decimal
import sys
import os
import pytest

# Add parent directory to path to import lib
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.fiscal_engine import validate_copropiedad, calculate_isai, calculate_retentions, sanitize_name

def test_validate_copropiedad():
    # Exact 100
    assert validate_copropiedad([Decimal('50.00'), Decimal('50.00')]) == True
    assert validate_copropiedad([Decimal('33.33'), Decimal('33.33'), Decimal('33.34')]) == True

    # Inexact
    assert validate_copropiedad([Decimal('50.00'), Decimal('49.99')]) == False
    assert validate_copropiedad([Decimal('100.01')]) == False

def test_calculate_isai():
    # Price > Catastral
    # Max(100, 80) * 0.03 = 3.00
    assert calculate_isai(Decimal('100.00'), Decimal('80.00')) == Decimal('3.00')

    # Catastral > Price
    # Max(100, 120) * 0.03 = 3.60
    assert calculate_isai(Decimal('100.00'), Decimal('120.00')) == Decimal('3.60')

def test_calculate_retentions_persona_moral():
    # RFC 12 chars
    rfc = "ABC123456T12"
    subtotal = Decimal('1000.00')
    rets = calculate_retentions(subtotal, rfc)

    # ISR 10% = 100.00
    assert rets['isr_ret'] == Decimal('100.00')

    # IVA 10.6667% = 106.67 (rounded)
    # 1000 * 0.106667 = 106.667 -> 106.67
    assert rets['iva_ret'] == Decimal('106.67')

def test_calculate_retentions_persona_fisica():
    # RFC 13 chars
    rfc = "ABCD123456T12"
    subtotal = Decimal('1000.00')
    rets = calculate_retentions(subtotal, rfc)

    assert rets['isr_ret'] == Decimal('0.00')
    assert rets['iva_ret'] == Decimal('0.00')

def test_sanitize_name():
    assert sanitize_name("Inmobiliaria Del Pacifico, S.A. DE C.V.") == "INMOBILIARIA DEL PACIFICO"
    assert sanitize_name("  Empresa Fantasma S.A.  ") == "EMPRESA FANTASMA"
    assert sanitize_name("JUAN PEREZ") == "JUAN PEREZ"

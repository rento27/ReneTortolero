import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from decimal import Decimal
from lib.fiscal_engine import sanitize_name, get_retention_rates, calculate_isai, validate_copropiedad, validate_postal_code_structure

def test_validate_postal_code_structure():
    assert validate_postal_code_structure("28200") == True
    assert validate_postal_code_structure("1234") == False # Too short
    assert validate_postal_code_structure("123456") == False # Too long
    assert validate_postal_code_structure("ABCDE") == False # Not digits
    assert validate_postal_code_structure("") == False

def test_sanitize_name():
    assert sanitize_name("INMOBILIARIA DEL PACÍFICO, S.A. DE C.V.") == "INMOBILIARIA DEL PACIFICO"
    assert sanitize_name("EMPRESA S.C.") == "EMPRESA"
    assert sanitize_name("JUAN PEREZ") == "JUAN PEREZ"
    assert sanitize_name("") == ""

def test_retention_rates():
    # Persona Moral
    rates = get_retention_rates("ABC123456789")
    assert rates['isr'] == Decimal("0.10")
    assert rates['iva'] == Decimal("0.106667")

    # Persona Fisica
    rates = get_retention_rates("ABCD123456789")
    assert rates['isr'] == Decimal("0.00")
    assert rates['iva'] == Decimal("0.00")

def test_isai():
    # Max(100, 200) * 0.03 = 200 * 0.03 = 6.00
    assert calculate_isai(Decimal("100"), Decimal("200")) == Decimal("6.00")
    # Max(300, 200) * 0.03 = 300 * 0.03 = 9.00
    assert calculate_isai(Decimal("300"), Decimal("200")) == Decimal("9.00")

def test_copropiedad():
    assert validate_copropiedad([Decimal("50.00"), Decimal("50.00")]) == True
    assert validate_copropiedad([Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]) == True
    assert validate_copropiedad([Decimal("33.33"), Decimal("33.33"), Decimal("33.33")]) == False

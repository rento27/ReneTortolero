import sys
import os
from decimal import Decimal

# Add current directory to path to allow imports from lib
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lib.fiscal_engine import calculate_fiscal_data, validate_copropiedad, sanitize_name

def test_persona_moral_logic():
    print("Testing Persona Moral Logic...")
    # RFC length 12
    rfc = "ABC123456789"

    # Using dummy values for base honorarios inside the function (1000.00)
    # The function returns:
    # ISR: 1000 * 0.10 = 100.00
    # IVA: 1000 * 0.16 = 160.00. Retained: (160/3)*2 = 106.666... -> 106.67

    result = calculate_fiscal_data(rfc, 10000.0, 5000.0)
    retentions = result['retentions']

    print(f"Result: {retentions}")

    assert retentions['isr_amount'] == 100.00, f"Expected ISR 100.00, got {retentions['isr_amount']}"
    assert retentions['iva_retenido_amount'] == 106.67, f"Expected IVA Ret 106.67, got {retentions['iva_retenido_amount']}"
    print("PASS: Persona Moral Retentions verified.")

def test_isai_logic():
    print("\nTesting ISAI Logic...")
    # Max(10000, 5000) = 10000
    # Rate 0.03
    # ISAI = 300.00
    result = calculate_fiscal_data("ABCD123456789", 10000.0, 5000.0)
    isai = result['isai_calculation']

    print(f"Result: {isai}")

    assert isai['amount'] == 300.00, f"Expected ISAI 300.00, got {isai['amount']}"
    print("PASS: ISAI Calculation verified.")

def test_copropiedad():
    print("\nTesting Copropiedad Logic...")
    # 50 + 50 = 100
    valid = validate_copropiedad([Decimal("50.00"), Decimal("50.00")])
    assert valid == True, "50+50 should be valid"

    # 33.33 + 33.33 + 33.33 = 99.99 -> False
    invalid = validate_copropiedad([Decimal("33.33"), Decimal("33.33"), Decimal("33.33")])
    assert invalid == False, "99.99 should be invalid"

    # 33.33 + 33.33 + 33.34 = 100.00 -> True
    valid_complex = validate_copropiedad([Decimal("33.33"), Decimal("33.33"), Decimal("33.34")])
    assert valid_complex == True, "33.33+33.33+33.34 should be valid"
    print("PASS: Copropiedad Logic verified.")

def test_sanitize_name():
    print("\nTesting Name Sanitization...")
    name = "INMOBILIARIA DEL PACIFICO, S.A. DE C.V."
    clean = sanitize_name(name)
    assert clean == "INMOBILIARIA DEL PACIFICO", f"Failed: {clean}"

    name2 = "GRUPO INDUSTRIAL, S.A.P.I. DE C.V."
    clean2 = sanitize_name(name2)
    assert clean2 == "GRUPO INDUSTRIAL", f"Failed: {clean2}"

    print("PASS: Name Sanitization verified.")

if __name__ == "__main__":
    test_persona_moral_logic()
    test_isai_logic()
    test_copropiedad()
    test_sanitize_name()
    print("\nALL TESTS PASSED.")

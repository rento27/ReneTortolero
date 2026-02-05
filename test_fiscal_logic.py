import sys
import os
from decimal import Decimal, getcontext

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'notaria_4_core/backend')))

from lib.fiscal_engine import calculate_retentions

# Set precision
getcontext().prec = 50

def test_fiscal_logic_with_mixed_concepts():
    print("Testing Fiscal Logic with Mixed Concepts...")

    # Scenario:
    # Item 1: Honorarios $1000.00 (Taxable '02')
    # Item 2: Suplidos $500.00 (Non-Taxable '01')

    concepts = [
        {'importe': Decimal("1000.00"), 'objeto_imp': '02'},
        {'importe': Decimal("500.00"), 'objeto_imp': '01'}
    ]

    # Logic implemented in main.py / xml_generator.py
    taxable_base = sum(c['importe'] for c in concepts if c['objeto_imp'] == '02')

    print(f"Calculated Taxable Base: {taxable_base}")
    if taxable_base != Decimal("1000.00"):
        print(f"FAIL: Taxable Base Calculation. Expected 1000.00, got {taxable_base}")
        return

    rfc_moral = "AAA010101AAA" # 12 chars

    # Call the refactored function
    retentions = calculate_retentions(rfc_receptor=rfc_moral, taxable_base=taxable_base)

    print(f"Calculated Retentions: {retentions}")

    # Expected:
    # ISR: 10% of 1000 = 100.00
    # IVA: 2/3 of (1000 * 0.16) = 2/3 of 160 = 106.67

    expected_isr = Decimal("100.00")
    expected_iva_ret = Decimal("106.67")

    if retentions['isr'] != expected_isr:
        print(f"FAIL: ISR Retention mismatch. Expected {expected_isr}, got {retentions['isr']}")
    else:
        print("PASS: ISR Retention matches.")

    if retentions['iva'] != expected_iva_ret:
        print(f"FAIL: IVA Retention mismatch. Expected {expected_iva_ret}, got {retentions['iva']}")
    else:
        print("PASS: IVA Retention matches.")

if __name__ == "__main__":
    test_fiscal_logic_with_mixed_concepts()

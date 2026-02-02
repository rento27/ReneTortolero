import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List

def sanitize_name(name: str) -> str:
    """
    Sanitizes the receiver name for CFDI 4.0 strict validation.
    Removes corporate regimes like 'S.A. DE C.V.' and normalizes text.
    """
    if not name:
        return ""

    # Normalize unicode characters (remove accents)
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')

    # Uppercase
    name = name.upper().strip()

    # List of common corporate regimes to remove
    # Regex pattern looks for these at the end of the string, preceded by optional comma or space
    regimes = [
        r"S\.?A\.? DE C\.?V\.?",
        r"S\.?A\.?P\.?I\.? DE C\.?V\.?",
        r"S\.? DE R\.?L\.? DE C\.?V\.?",
        r"S\.?A\.?B\.? DE C\.?V\.?",
        r"S\.?A\.?",
        r"S\.?C\.?",
        r"A\.?C\.?",
        r"S\.?A\.?S\.?",
        r"L\.?T\.?D\.?",
        r"INC\.?"
    ]

    for regime in regimes:
        # \s* matches spaces, ,? matches optional comma
        # $ anchors to end of string
        pattern = r"[\s,]*" + regime + r"$"
        name = re.sub(pattern, "", name)

    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name).strip()

    return name

def calculate_taxes(subtotal: Decimal, rfc_receptor: str) -> Dict[str, Any]:
    """
    Calculates taxes based on receptor type (Persona Fisica vs Moral).
    """
    # Ensure subtotal is Decimal
    if not isinstance(subtotal, Decimal):
        subtotal = Decimal(str(subtotal))

    # Standard IVA rate
    iva_rate = Decimal('0.16')

    iva_trasladado = (subtotal * iva_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    total = subtotal + iva_trasladado

    result = {
        "subtotal": subtotal,
        "iva_trasladado": iva_trasladado,
        "retenciones": [],
        "total_previo": total, # Before retentions
        "total": total
    }

    # Persona Moral Logic (RFC length 12)
    if len(rfc_receptor) == 12:
        # ISR Retention: 10%
        isr_ret_rate = Decimal('0.10')
        isr_ret = (subtotal * isr_ret_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # IVA Retention: 2/3 of IVA Trasladado
        # Mathematically: IVA_Trasladado * (2/3) or 10.6667%
        # The prompt mentions: "$6,083.91 * 0.10 = $608.39" and "Two thirds of VAT"

        # Method A: Calculate from base (10.6667%) - commonly used but strictly it's 2/3 of tax
        # Method B: Calculate 2/3 of the calculated IVA amount.

        # SAT usually expects rate 0.106666 or similar.
        # Let's use the explicit rate mentioned in requirements if possible, or 2/3.
        # Requirement says: "Matemáticamente, esto equivale a una tasa del 10.6667%."
        iva_ret_rate = Decimal('0.106667')
        iva_ret = (subtotal * iva_ret_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        result["retenciones"] = [
            {"impuesto": "001", "impuesto_nombre": "ISR", "tasa": isr_ret_rate, "importe": isr_ret},
            {"impuesto": "002", "impuesto_nombre": "IVA", "tasa": iva_ret_rate, "importe": iva_ret}
        ]

        result["total"] = total - isr_ret - iva_ret

    return result

def calculate_isai(precio_operacion: Decimal, valor_catastral: Decimal, tasa: Decimal = Decimal('0.03')) -> Decimal:
    """
    Calculates ISAI for Manzanillo.
    ISAI = Max(Price, Catastral) * Rate
    """
    base = max(precio_operacion, valor_catastral)
    impuesto = base * tasa
    return impuesto.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def validate_copropiedad(percentages: List[Decimal]) -> bool:
    """
    Validates that the sum of copropiedad percentages equals exactly 100.00%.
    """
    total = sum(percentages)
    target = Decimal('100.00')

    # Compare with a very small tolerance or exact
    # Requirement says "Sum(Porcentajes) == 100.00%" strictly.
    # We use quantized comparison to handle potential float inputs converted to Decimal

    total_quantized = total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return total_quantized == target

def validate_zip_code(zip_code: str, state_code: str = "06") -> bool:
    """
    Validates ZIP code structure and cross-references with State code.
    Default state_code '06' is Colima.
    """
    if not zip_code or not zip_code.isdigit() or len(zip_code) != 5:
        return False

    # Colima specific rule: Zips start with 28
    if state_code == "06" and not zip_code.startswith("28"):
        return False

    return True

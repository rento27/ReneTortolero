import re
from decimal import Decimal, getcontext, ROUND_HALF_UP

# Set precision for fiscal calculations
# Using 50 to avoid rounding errors in high-value real estate transactions
getcontext().prec = 50

def sanitize_name(name: str) -> str:
    """
    Normalizes the name for CFDI 4.0:
    1. Removes corporate regime suffixes (e.g., S.A. DE C.V.).
    2. Removes extra whitespace.
    3. Removes trailing punctuation.
    """
    if not name:
        return ""

    # Uppercase
    name = name.upper().strip()

    # Common corporate regimes to remove (must be anchored to end or followed by punctuation)
    # Note: The list can be expanded.
    regimes = [
        r"\s+S\.?A\.?\s+DE\s+C\.?V\.?$",
        r"\s+S\.?A\.?$",
        r"\s+S\.?C\.?$",
        r"\s+S\.?C\.?\s+DE\s+R\.?L\.?$",
        r"\s+S\.?A\.?P\.?I\.?\s+DE\s+C\.?V\.?$",
        r"\s+LTD\.?$",
        r"\s+INC\.?$",
        r"\s+S\.? DE R\.?L\.? DE C\.?V\.?$"
    ]

    for regime in regimes:
        name = re.sub(regime, "", name)

    # Remove trailing punctuation (periods, commas)
    name = re.sub(r"[\.,]+$", "", name)

    return name.strip()

def calculate_retentions_persona_moral(subtotal: Decimal, rfc_receptor: str, iva_rate: Decimal = Decimal('0.16')):
    """
    Calculates retentions if the receptor is a Persona Moral (RFC length 12).
    Returns a dictionary with retention amounts.
    """
    if not rfc_receptor:
        return None

    clean_rfc = rfc_receptor.strip().upper()

    # Persona Moral has 12 chars, Fisica has 13.
    if len(clean_rfc) == 12:
        # ISR Retention: 10%
        isr_retention = subtotal * Decimal('0.10')

        # IVA Retention: 2/3 of the IVA amount
        iva_amount = subtotal * iva_rate
        # The prompt mentions "Regla de los Dos Tercios"
        iva_retention = iva_amount * (Decimal('2') / Decimal('3'))

        return {
            "isr_retention": isr_retention.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "iva_retention": iva_retention.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        }

    return None

def calculate_isai_manzanillo(operation_price: Decimal, cadastral_value: Decimal, rate: Decimal = Decimal('0.03')) -> Decimal:
    """
    Calculates ISAI (Impuesto Sobre Adquisición de Inmuebles) for Manzanillo.
    Formula: Max(Price, Cadastral) * Rate
    """
    base = max(operation_price, cadastral_value)
    isai = base * rate
    return isai.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def validate_copropiedad(percentages: list[Decimal]) -> bool:
    """
    Validates that the sum of percentages equals exactly 100.00%.
    """
    total = sum(percentages)
    # Compare with a tolerance suitable for float but here we use Decimal so exact match is expected
    # However, inputs might be 33.33, 33.33, 33.34.
    return total == Decimal('100.00')

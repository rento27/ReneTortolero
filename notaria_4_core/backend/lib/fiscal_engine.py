import re
from decimal import Decimal, getcontext, ROUND_HALF_UP

# Set precision context as requested
getcontext().prec = 10

def sanitize_name(name: str) -> str:
    """
    Removes corporate regimes from the name to comply with CFDI 4.0 strict name matching.
    Example: 'INMOBILIARIA DEL PACÍFICO, S.A. DE C.V.' -> 'INMOBILIARIA DEL PACÍFICO'
    """
    if not name:
        return ""

    # Normalize to uppercase
    name = name.upper().strip()

    # Common corporate regimes in Mexico (Non-exhaustive list, focused on common ones)
    regimes = [
        r"S\.?A\.?\s+DE\s+C\.?V\.?",
        r"S\.?A\.?P\.?I\.?\s+DE\s+C\.?V\.?",
        r"S\.?\s+DE\s+R\.?L\.?\s+DE\s+C\.?V\.?",
        r"S\.?A\.?",
        r"S\.?C\.?",
        r"S\.?C\.?\s+DE\s+R\.?L\.?",
        r"S\.?A\.?S\.?",
        r"A\.?C\.?"
    ]

    # Construct regex pattern anchored at the end
    # We use \b to ensure word boundary
    pattern = r",?\s+(" + "|".join(regimes) + r")\.?$"

    clean_name = re.sub(pattern, "", name, flags=re.IGNORECASE)

    # Remove trailing punctuation like commas or periods
    clean_name = clean_name.strip(" .,")

    return clean_name

def validate_copropiedad(percentages: list[Decimal]) -> bool:
    """
    Validates that the sum of copropiedad percentages equals EXACTLY 100.00%.
    """
    total = sum(percentages)
    # Strict comparison
    return total == Decimal('100.00')

def calculate_isai(precio_operacion: Decimal, valor_catastral: Decimal, tasa: Decimal = Decimal('0.03')) -> Decimal:
    """
    Calculates ISAI Manzanillo.
    Formula: Max(Price, Cadastral) * Rate
    """
    base = max(precio_operacion, valor_catastral)
    return (base * tasa).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calculate_retentions(subtotal: Decimal, rfc_receptor: str) -> dict:
    """
    Calculates retentions for Personas Morales (RFC length 12).
    ISR: 10%
    IVA: 2/3 of IVA (10.6667%)
    """
    # Basic validation of RFC length
    clean_rfc = rfc_receptor.strip().upper()

    if len(clean_rfc) == 12:
        # Persona Moral
        isr_ret = subtotal * Decimal('0.10')
        # 2/3 of IVA (16%) -> 10.66666... The prompt specifies 10.6667% explicitly
        iva_ret = subtotal * Decimal('0.106667')

        return {
            "isr_ret": isr_ret.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            "iva_ret": iva_ret.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        }

    # Persona Física or generic
    return {
        "isr_ret": Decimal('0.00'),
        "iva_ret": Decimal('0.00')
    }

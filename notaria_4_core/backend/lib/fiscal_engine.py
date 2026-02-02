from decimal import Decimal, getcontext, ROUND_HALF_UP
import re
import unicodedata

# Set global precision as per strict fiscal requirements to avoid rounding errors
getcontext().prec = 50

# Default rounding mode for currency
ROUNDING_MODE = ROUND_HALF_UP

def calculate_isai_manzanillo(price: Decimal, cadastral_value: Decimal, rate: Decimal = Decimal('0.03')) -> Decimal:
    """
    Calculates ISAI (Impuesto Sobre Adquisición de Inmuebles) for Manzanillo.
    Formula: Max(Price, Cadastral) * Rate

    Args:
        price: The operation price from the deed.
        cadastral_value: The cadastral value.
        rate: The tax rate (default 3%).

    Returns:
        Decimal: The calculated tax rounded to 2 decimal places.
    """
    base = max(price, cadastral_value)
    tax = base * rate
    return tax.quantize(Decimal('0.01'), rounding=ROUNDING_MODE)

def get_retention_rates(rfc: str) -> dict:
    """
    Determines retention rates based on RFC length (Persona Moral vs Física).

    Args:
        rfc: The RFC string.

    Returns:
        dict: containing 'isr_rate' and 'iva_rate' as Decimals.
    """
    clean_rfc = rfc.strip().upper()

    # Persona Moral has 12 characters
    if len(clean_rfc) == 12:
        # ISR: 10%
        # IVA: 2/3 of the 16% VAT rate
        # 0.16 * 2/3 = 0.106666...
        return {
            "isr_rate": Decimal('0.10'),
            "iva_rate": (Decimal('0.16') * Decimal('2') / Decimal('3'))
        }

    # Persona Física (13 chars) or generic foreign RFC
    return {
        "isr_rate": Decimal('0.00'),
        "iva_rate": Decimal('0.00')
    }

def validate_copropiedad(percentages: list[Decimal]) -> bool:
    """
    Validates that the sum of ownership percentages is exactly 100.00.

    Args:
        percentages: A list of Decimal values representing ownership %.

    Returns:
        bool: True if sum is exactly 100.00, False otherwise.
    """
    total = sum(percentages)
    # Check if total equals 100.00 exactly.
    # Note: We compare against a Decimal to ensure type safety.
    return total == Decimal('100.00')

def sanitize_name(name: str) -> str:
    """
    Sanitizes the name for CFDI 4.0 compliance.
    - Removes corporate regimes (e.g., 'S.A. DE C.V.')
    - Removes punctuation.
    - Normalizes spaces.
    - Converts to Uppercase.

    Args:
        name: The raw name string.

    Returns:
        str: The sanitized name.
    """
    if not name:
        return ""

    name = name.upper().strip()

    # Normalize unicode to decompose accents (NFD) and filter non-spacing marks (Mn)
    name = unicodedata.normalize('NFD', name)
    name = "".join([c for c in name if unicodedata.category(c) != 'Mn'])

    # Common corporate suffixes to remove.
    # Ordered by length to catch longer matches first (e.g. S.A.P.I. DE C.V. before S.A.)
    suffixes = [
        r"\s+S\.?\s?A\.?\s+P\.?\s?I\.?\s+DE\s+C\.?\s?V\.?", # S.A.P.I. DE C.V.
        r"\s+S\.?\s?A\.?\s+DE\s+C\.?\s?V\.?",               # S.A. DE C.V.
        r"\s+S\.?\s?C\.?\s+DE\s+R\.?\s?L\.?\s+DE\s+C\.?\s?V\.?", # S.C. DE R.L. DE C.V.
        r"\s+S\.?\s?DE\s+R\.?\s?L\.?\s+DE\s+C\.?\s?V\.?",   # S. DE R.L. DE C.V.
        r"\s+S\.?\s?A\.?S\.?",                              # S.A.S.
        r"\s+S\.?\s?C\.?",                                  # S.C.
        r"\s+S\.?\s?A\.?",                                  # S.A.
        r"\s+A\.?\s?C\.?",                                  # A.C.
        r"\s+I\.?\s?A\.?\s?P\.?",                           # I.A.P.
        r"\s+S\.?\s?N\.?\s?C\.?"                            # S.N.C.
    ]

    # Iteratively remove suffixes found at the END of the string
    for suffix in suffixes:
        # Use sub with $ anchor
        new_name = re.sub(suffix + "$", "", name)
        if len(new_name) < len(name):
            name = new_name
            break # Assume only one regime suffix

    # Remove punctuation: . , ; :
    name = re.sub(r"[.,;:]", "", name)

    # Collapse multiple spaces into one
    name = re.sub(r"\s+", " ", name)

    return name.strip()

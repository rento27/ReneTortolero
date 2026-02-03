import re
from decimal import Decimal, ROUND_HALF_UP, getcontext

# Set precision context to avoid off-by-one errors in large transactions
getcontext().prec = 50

# Manzanillo ISAI Rate (Default)
ISAI_RATE_MANZANILLO = Decimal("0.03")

# Regex for Corporate Regimes.
# Matches common suffixes like " S.A. DE C.V.", ", S.C.", " S.A.B. DE C.V." etc. at the end of the string.
# It handles optional commas and variations in punctuation.
REGIME_REGEX = re.compile(r"([,\s]+(S\.?A\.?|S\.?C\.?|S\.?R\.?L\.?|S\.?A\.?B\.?|S\.?N\.?C\.?|A\.?C\.?|I\.?A\.?P\.?|S\.?A\.?P\.?I\.?)(\s+DE\s+(C\.?V\.?|R\.?L\.?|I\.?P\.?))?)+$", re.IGNORECASE)

# Standard Rounding for Currency
ROUNDING_MODE = ROUND_HALF_UP

def sanitize_name(name: str) -> str:
    """
    Sanitizes the name for CFDI 4.0 strict validation.
    Removes corporate regime (e.g. 'S.A. DE C.V.') and cleans whitespace.

    Args:
        name: The full name or reason social.

    Returns:
        The sanitized name compatible with SAT strict validation (excluding regime).
    """
    if not name:
        return ""

    # Remove regime using the regex
    clean_name = REGIME_REGEX.sub("", name)

    # Remove extra internal whitespace and trailing/leading whitespace
    clean_name = re.sub(r"\s+", " ", clean_name).strip()

    # Remove trailing punctuation (commas, periods) that might remain after regime removal
    clean_name = clean_name.rstrip(".,")

    return clean_name

def calculate_isai_manzanillo(price: Decimal, cadastral_value: Decimal, rate: Decimal = ISAI_RATE_MANZANILLO) -> Decimal:
    """
    Calculates ISAI for Manzanillo.
    Formula: Max(Price, Cadastral) * Rate

    Args:
        price: Transaction price (Operacion).
        cadastral_value: Cadastral value of the property.
        rate: Tax rate (default 0.03).

    Returns:
        The calculated ISAI tax amount rounded to 2 decimals.
    """
    base = max(price, cadastral_value)
    tax = base * rate
    return tax.quantize(Decimal("0.01"), rounding=ROUNDING_MODE)

def get_retention_rates(rfc: str) -> dict:
    """
    Determines retention rates based on RFC type (Persona Moral vs Fisica).
    Persona Moral (12 chars) -> Retain ISR and IVA.

    Args:
        rfc: The Receptor RFC.

    Returns:
        Dictionary with 'isr' and 'iva' rates (Decimal).
    """
    if not rfc:
        return {"isr": Decimal("0.00"), "iva": Decimal("0.00")}

    clean_rfc = rfc.strip().upper()

    if len(clean_rfc) == 12:
        # Persona Moral
        return {
            "isr": Decimal("0.10"), # 10%
            "iva": Decimal("0.106667") # 2/3 of 16% = 0.106666... approx 0.106667
        }

    return {"isr": Decimal("0.00"), "iva": Decimal("0.00")}

def validate_copropiedad(percentages: list[Decimal]) -> bool:
    """
    Validates that the sum of percentages equals exactly 100.00%.
    Used for checking integrity of 'DatosAdquirientesCopSC'.

    Args:
        percentages: List of ownership percentages.

    Returns:
        True if sum is exactly 100.00, False otherwise.
    """
    total = sum(percentages)
    # Using strict equality as per prompt requirement "Sum(Porcentajes) == 100.00%"
    return total == Decimal("100.00")

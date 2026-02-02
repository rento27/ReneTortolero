import re
import unicodedata
from decimal import Decimal, getcontext, ROUND_HALF_UP

# Set precision high enough to avoid intermediate rounding errors
getcontext().prec = 10

def sanitize_name(name: str) -> str:
    """
    Removes corporate regime suffixes (e.g., S.A. DE C.V.) and normalizes text
    for CFDI 4.0 strict name matching.
    """
    if not name:
        return ""

    # Normalize unicode (e.g. accents)
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')
    name = name.upper().strip()

    # Regex patterns for common Mexican corporate regimes
    # Note: These must be anchored or spaced correctly to avoid partial matches inside names
    regimes = [
        r"\s+S\.?\s?A\.?\s+DE\s+C\.?\s?V\.?",   # S.A. DE C.V.
        r"\s+S\.?\s?A\.?\s+DE\s+C\.?V\.?",     # S.A. DE CV
        r"\s+S\.?\s?A\.?",                      # S.A.
        r"\s+S\.?\s?C\.?",                      # S.C.
        r"\s+S\.?\s?A\.?\s+P\.?\s?I\.?\s+DE\s+C\.?\s?V\.?", # S.A.P.I. DE C.V.
        r"\s+L\.?T\.?D\.?",                     # LTD
        r"\s+S\.?\s?DE\s+R\.?L\.?\s+DE\s+C\.?\s?V\.?", # S. DE R.L. DE C.V.
        r"\s+S\.?\s?DE\s+R\.?L\.?"              # S. DE R.L.
    ]

    clean_name = name
    for pattern in regimes:
        clean_name = re.sub(pattern, "", clean_name, flags=re.IGNORECASE)

    # Remove extra spaces
    clean_name = re.sub(r"\s+", " ", clean_name).strip()

    # Remove trailing punctuation often left behind (commas, periods)
    clean_name = clean_name.rstrip(",.")

    return clean_name

def calculate_isai(precio_operacion: Decimal, valor_catastral: Decimal, tasa: Decimal = Decimal("0.03")) -> Decimal:
    """
    Calculates ISAI for Manzanillo.
    Formula: Max(Precio, ValorCatastral) * Tasa
    """
    base = max(precio_operacion, valor_catastral)
    isai = base * tasa
    return isai.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def calculate_retentions(rfc_receptor: str, subtotal: Decimal) -> dict:
    """
    Calculates tax retentions based on Receptor RFC length.
    If RFC is 12 characters (Persona Moral), applies retentions.
    """
    retentions = {
        "ret_isr": Decimal("0.00"),
        "ret_iva": Decimal("0.00"),
        "is_moral": False
    }

    clean_rfc = rfc_receptor.strip().upper()

    if len(clean_rfc) == 12:
        retentions["is_moral"] = True
        # ISR Retention: 10%
        retentions["ret_isr"] = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # IVA Retention: 2/3 of 16% (approx 10.6667%)
        # Exact calculation: Subtotal * 0.16 * (2/3)
        iva_total = subtotal * Decimal("0.16")
        ret_iva = iva_total * (Decimal("2") / Decimal("3"))
        retentions["ret_iva"] = ret_iva.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return retentions

def validate_copropiedad(percentages: list[Decimal]) -> bool:
    """
    Validates that the sum of percentages equals exactly 100.00%
    """
    total = sum(percentages)
    # Check if total equals 100 within a very small tolerance, though Decimal should be exact
    return total == Decimal("100.00")

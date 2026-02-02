from decimal import Decimal, ROUND_HALF_UP
import re
import unicodedata

# Constants for Manzanillo ISAI (Should ideally come from config/DB)
DEFAULT_ISAI_RATE_MANZANILLO = Decimal("0.03")

def sanitize_name(name: str) -> str:
    """
    Sanitizes the name for CFDI 4.0 strict validation.
    Removes corporate regimes like 'S.A. DE C.V.'
    Removes accents and trailing punctuation.
    """
    # 1. Normalize accents (NFD -> NFC or just strip accents)
    name = unicodedata.normalize('NFD', name)
    name = "".join(c for c in name if unicodedata.category(c) != 'Mn')

    name = name.upper().strip()

    # 2. Remove corporate regimes
    # Regex to remove common corporate suffixes
    # Matches " S.A. DE C.V.", " S.C.", etc. at the end of the string
    regimes = [
        r"\s+S\.?\s*A\.?\s+DE\s+C\.?\s*V\.?\.?$",
        r"\s+S\.?\s*A\.?\s+P\.?\s*I\.?\s+DE\s+C\.?\s*V\.?\.?$",
        r"\s+S\.?\s*C\.?\.?$",
        r"\s+S\.?\s*A\.?\.?$",
        r"\s+A\.?\s*C\.?\.?$"
    ]

    for pattern in regimes:
        name = re.sub(pattern, "", name, flags=re.IGNORECASE)

    # 3. Clean trailing punctuation (commas, periods) that might remain
    name = name.strip(" ,.")

    return name.strip()

def calculate_isai(precio_operacion: Decimal, valor_catastral: Decimal, rate: Decimal = DEFAULT_ISAI_RATE_MANZANILLO) -> Decimal:
    """
    Calculates ISAI for Manzanillo.
    ISAI = Max(Precio, ValorCatastral) * Rate
    """
    base = max(precio_operacion, valor_catastral)
    return (base * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def calculate_retentions_persona_moral(subtotal: Decimal, rfc: str) -> dict:
    """
    Calculates retentions if the RFC indicates a Persona Moral (len == 12).
    ISR: 10%
    IVA: 10.6667% (2/3 of 16%)
    """
    if len(rfc.strip()) != 12:
        return {}

    isr_retention = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # 10.6667% is the approximation of 2/3 of 16% (0.16 * 2/3 = 0.106666...)
    # We use a high precision Decimal for the factor to ensure accuracy
    iva_factor = Decimal("2") / Decimal("3") * Decimal("0.16")
    iva_retention = (subtotal * iva_factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "ret_isr": isr_retention,
        "ret_iva": iva_retention
    }

def validate_copropiedad(percentages: list[Decimal]) -> bool:
    """
    Validates that the sum of copropiedad percentages is exactly 100.00%.
    """
    total = sum(percentages)
    return total == Decimal("100.00")

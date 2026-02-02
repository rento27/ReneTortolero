import re
from decimal import Decimal, getcontext, ROUND_HALF_UP

# Set strict decimal precision
getcontext().prec = 28

def sanitize_name(name: str) -> str:
    """
    Removes corporate regime suffixes from the name for CFDI 4.0 validation.
    Example: "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACÍFICO"
    """
    if not name:
        return ""

    clean_name = name.strip()

    # List of common regimes to strip (Case insensitive).
    # ORDER MATTERS: Longer matches first to avoid partial stripping.
    # MUST be anchored to end of string ($) to prevent matching inside names (e.g. "AC" in "PACIFICO")
    regimes = [
        r",?\s*S\.?A\.?P\.?I\.?\s*DE\s*C\.?V\.?$",
        r",?\s*S\.?A\.?\s*DE\s*C\.?V\.?$",
        r",?\s*S\.? DE R\.?L\.? DE C\.?V\.?$",
        r",?\s*S\.?A\.?$",
        r",?\s*S\.?C\.?$",
        r",?\s*A\.?C\.?$",
        r",?\s*L\.?T\.?D\.?$",
        r",?\s*INC\.?$"
    ]

    # Loop to handle cases where multiple might exist (rare) or just apply once.
    # Usually just one match at the end.
    for regime in regimes:
        clean_name = re.sub(regime, "", clean_name, flags=re.IGNORECASE)

    # Remove trailing punctuation and extra spaces
    clean_name = re.sub(r"[,.]$", "", clean_name).strip()

    return clean_name.upper()

def calculate_retentions(rfc: str, subtotal: Decimal) -> dict:
    """
    Calculates retentions if the RFC belongs to a Persona Moral (12 chars).
    """
    if len(rfc) == 12:
        # Persona Moral
        isr_retention = subtotal * Decimal("0.10")

        # IVA Retention: 10.6667%
        iva_retention = subtotal * Decimal("0.106667")

        return {
            "retencion_isr": isr_retention.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "retencion_iva": iva_retention.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "is_persona_moral": True
        }

    return {
        "retencion_isr": Decimal("0.00"),
        "retencion_iva": Decimal("0.00"),
        "is_persona_moral": False
    }

def validate_copropiedad(percentages: list[Decimal]) -> bool:
    """
    Validates that the sum of copropiedad percentages is exactly 100.00%.
    """
    total = sum(percentages)
    target = Decimal("100.00")

    return total == target

def calculate_isai(precio_operacion: Decimal, valor_catastral: Decimal, tasa: Decimal) -> Decimal:
    """
    Calculates ISAI based on Manzanillo rules: Max(Price, Catastral) * Tasa
    """
    base = max(precio_operacion, valor_catastral)
    isai = base * tasa
    return isai.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

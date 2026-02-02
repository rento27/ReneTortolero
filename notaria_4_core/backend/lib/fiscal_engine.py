import re
from decimal import Decimal, getcontext, ROUND_HALF_UP
from typing import List, Dict, Union

# Set global precision
getcontext().prec = 10

def sanitize_name(name: str) -> str:
    """
    Removes corporate regimes from the name to comply with CFDI 4.0 strict validation.
    Example: "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACIFICO"
    """
    if not name:
        return ""

    # Normalize spaces
    clean_name = " ".join(name.split())

    # Regex to remove common suffixes at the end of the string
    # Matches comma optionally, then space, then the regime patterns
    # Handles: S.A., S.A. DE C.V., S.C., S. DE R.L. DE C.V., etc.
    # We use a pattern that matches the specific "legal entity" endings.
    # Note: This is a heuristic and might need refinement based on specific Notary data.

    patterns = [
        r",?\s*S\.?A\.?\s*DE\s*C\.?V\.?$",
        r",?\s*S\.?A\.?$",
        r",?\s*S\.?C\.?$",
        r",?\s*S\.?A\.?S\.?$",
        r",?\s*S\.?\s*DE\s*R\.?L\.?\s*DE\s*C\.?V\.?$",
        r",?\s*S\.?\s*DE\s*R\.?L\.?$",
        r",?\s*INC\.?$",
        r",?\s*LTD\.?$"
    ]

    for pattern in patterns:
        clean_name = re.sub(pattern, "", clean_name, flags=re.IGNORECASE)

    # Remove trailing punctuation often left behind
    clean_name = clean_name.strip(" .,")

    return clean_name.upper()

def calculate_retentions(subtotal: Decimal, rfc_receptor: str) -> Dict[str, Decimal]:
    """
    Calculates ISR and IVA retentions for Personas Morales (RFC len 12).
    """
    retentions = {
        "ISR": Decimal("0.00"),
        "IVA": Decimal("0.00")
    }

    # Persona Moral check (12 characters)
    if len(rfc_receptor) == 12:
        # ISR: 10%
        retentions["ISR"] = subtotal * Decimal("0.10")

        # IVA: 2/3 of IVA (which is 16%)
        # Logic: Base * 0.16 * (2/3)
        iva_trasladado = subtotal * Decimal("0.16")
        retentions["IVA"] = iva_trasladado * Decimal("2") / Decimal("3")

    return retentions

def calculate_isai(precio_operacion: Decimal, valor_catastral: Decimal, tasa: Decimal = Decimal("0.03")) -> Decimal:
    """
    Calculates ISAI (Impuesto Sobre Adquisición de Inmuebles).
    Formula: Max(Precio, ValorCatastral) * Tasa
    """
    base_gravable = max(precio_operacion, valor_catastral)
    return base_gravable * tasa

def validate_copropiedad(percentages: List[Decimal]) -> bool:
    """
    Validates that the sum of percentages equals exactly 100.00%.
    """
    total = sum(percentages)

    # We compare with a tolerance but the requirement says "Exactamente" (Exactly).
    # Using Decimal, 100.00 should be exact.
    target = Decimal("100.00")

    return total == target

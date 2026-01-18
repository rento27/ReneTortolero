import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP

def sanitize_name(name: str) -> str:
    """
    Removes corporate regimes from the name to match SAT 4.0 strict validation.
    Example: "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACÍFICO"
    """
    # Normalize unicode (remove accents)
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')

    # Normalize spaces
    name = re.sub(r'\s+', ' ', name).strip().upper()

    # Common regimes to strip (anchored at the end)
    # Note: This list should be expanded based on the full SAT catalog
    regimes = [
        r",?\s*S\.?A\.?\s*DE\s*C\.?V\.?$",
        r",?\s*S\.?A\.?B\.?\s*DE\s*C\.?V\.?$",
        r",?\s*S\.?C\.?$",
        r",?\s*S\.?C\.?\s*DE\s*R\.?L\.?$",
        r",?\s*S\.?C\.?\s*DE\s*R\.?L\.?\s*DE\s*C\.?V\.?$",
        r",?\s*S\.?A\.?$",
        r",?\s*A\.?C\.?$",
        r",?\s*S\.?A\.?P\.?I\.?\s*DE\s*C\.?V\.?$",
        r",?\s*L\.?T\.?D\.?$",
        r",?\s*INC\.?$"
    ]

    for pattern in regimes:
        name = re.sub(pattern, "", name)

    # Remove trailing punctuation
    name = name.strip(" .,")
    return name

def calculate_retentions(rfc_receptor: str, subtotal: Decimal, iva_trasladado: Decimal) -> dict:
    """
    Calculates retentions for Persona Moral (RFC length 12).
    Returns a dictionary with retention amounts.
    """
    if len(rfc_receptor) == 12:
        # Persona Moral
        isr_ret = (subtotal * Decimal("0.10")).quantize(Decimal("0.000001"))

        # IVA Retention: 2/3 of IVA
        # 0.16 * (2/3) = 0.106666...
        # Or calculate directly from the IVA amount
        iva_ret = (iva_trasladado * Decimal(2) / Decimal(3)).quantize(Decimal("0.000001"))

        return {
            "isr_retention": isr_ret.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "iva_retention": iva_ret.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "is_persona_moral": True
        }

    return {
        "isr_retention": Decimal("0.00"),
        "iva_retention": Decimal("0.00"),
        "is_persona_moral": False
    }

def calculate_isai_manzanillo(precio_operacion: Decimal, valor_catastral: Decimal, tasa: Decimal = Decimal("0.03")) -> Decimal:
    """
    Calculates ISAI for Manzanillo.
    ISAI = Max(Precio, Catastral) * Tasa
    """
    base = max(precio_operacion, valor_catastral)
    isai = base * tasa
    return isai.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def validate_copropiedad(percentages: list[Decimal]) -> bool:
    """
    Validates that the sum of copropiedad percentages is exactly 100.00%.
    """
    total = sum(percentages)
    # Allow a very small epsilon just in case, but business rule says "Exact"
    # Using string comparison for exact decimal match is safer for business rules
    return total.quantize(Decimal("0.01")) == Decimal("100.00")

def validate_zip_code(zip_code: str, state_code: str) -> bool:
    """
    Validates zip code format and basic cross-reference.
    This is a simplified version. In production, this would query the DB.
    """
    if not re.match(r"^\d{5}$", zip_code):
        return False

    # Example rule: Colima Zips start with 28
    if state_code == "COL" or state_code == "06":
        if not zip_code.startswith("28"):
            return False

    return True

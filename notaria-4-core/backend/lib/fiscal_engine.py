import re
from decimal import Decimal, getcontext, ROUND_HALF_UP

# Set precision context globally or locally
# SAT often uses up to 6 decimals internally, but currency is 2.
getcontext().prec = 10

def sanitize_name(name: str) -> str:
    """
    Removes corporate suffixes (S.A. DE C.V., etc.) from the name
    to comply with CFDI 4.0 strict validation which requires the name
    to match the SAT records exactly (usually without the Regime).
    """
    # List of common suffixes to strip.
    # Order matters: longer matches should be first to avoid partial replacements.
    suffixes = [
        r"\s+S\.?A\.?B\.?\s+DE\s+C\.?V\.?",
        r"\s+S\.?A\.?P\.?I\.?\s+DE\s+C\.?V\.?",
        r"\s+S\.?DE\s+R\.?L\.?\s+DE\s+C\.?V\.?",
        r"\s+S\.?A\.?\s+DE\s+C\.?V\.?",
        r"\s+S\.?C\.?\s+DE\s+R\.?L\.?\s+DE\s+C\.?V\.?",
        r"\s+S\.?C\.?\s+DE\s+P\.?",
        r"\s+S\.?A\.?S\.?",
        r"\s+S\.?N\.?C\.?",
        r"\s+S\.?C\.?",
        r"\s+A\.?C\.?",
        r"\s+S\.?A\.?",
        r"\s+LTD\.?",
        r"\s+INC\.?"
    ]

    clean_name = name.strip()

    # Iterate and remove. We use ignorecase.
    for pattern in suffixes:
        # We look for the pattern at the end of the string ($)
        regex = re.compile(pattern + "$", re.IGNORECASE)
        clean_name = regex.sub("", clean_name)

    return clean_name.strip()

def calculate_isai_manzanillo(precio_operacion: Decimal, valor_catastral: Decimal, tasa: Decimal) -> Decimal:
    """
    Calculates ISAI (Impuesto Sobre Adquisición de Inmuebles) for Manzanillo.
    Formula: Max(Precio, ValorCatastral) * Tasa
    """
    base_gravable = max(precio_operacion, valor_catastral)
    return (base_gravable * tasa).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def calculate_retentions(rfc_receptor: str, subtotal: Decimal, iva_trasladado: Decimal):
    """
    Calculates retentions if the receiver is a Persona Moral (RFC length 12).

    Rules:
    - ISR: 10% of Subtotal
    - IVA: 2/3 of IVA Trasladado (effectively 10.6667% of Subtotal if IVA is 16%)

    Returns a dictionary with retention amounts or None.
    """
    # Clean RFC just in case
    rfc = rfc_receptor.strip().upper()

    if len(rfc) == 12:
        # Persona Moral
        isr_retention = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # IVA Retention: 2/3 of the transferred IVA.
        # We calculate with high precision then round.
        iva_retention_raw = (iva_trasladado * Decimal("2") / Decimal("3"))
        iva_retention = iva_retention_raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "isr_amount": isr_retention,
            "iva_amount": iva_retention,
            "is_persona_moral": True
        }

    return {
        "isr_amount": Decimal("0.00"),
        "iva_amount": Decimal("0.00"),
        "is_persona_moral": False
    }

def validate_copropiedad(percentages: list[float]) -> bool:
    """
    Validates that the sum of percentages equals exactly 100.00%.
    Used for 'DatosAdquirientesCopSC'.
    """
    total = sum(percentages)
    # Using a small epsilon for float comparison, though in fiscal context we prefer Decimal.
    # Blueprint says "Strict validation".
    return abs(total - 100.00) < 0.001

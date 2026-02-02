import re
from decimal import Decimal, ROUND_HALF_UP

def calculate_isai(price: float, cadastral_value: float, rate: float = 0.03) -> float:
    """
    Calculates ISAI (Impuesto Sobre Adquisición de Inmuebles) for Manzanillo.
    Formula: Max(Price, Cadastral) * Rate.
    """
    base = max(price, cadastral_value)
    return round(base * rate, 2)

def calculate_retentions(rfc: str, subtotal: float) -> dict:
    """
    Calculates retentions for Personas Morales (RFC length 12).
    - ISR: 10%
    - IVA: 10.6667% (Two thirds of 16%)
    """
    if len(rfc) == 12:
        # Using Decimal for precision
        sub_decimal = Decimal(str(subtotal))

        # ISR Retention 10%
        isr = sub_decimal * Decimal("0.10")

        # IVA Retention 10.6667%
        iva_ret = sub_decimal * Decimal("0.106667")

        return {
            "isr": float(isr.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            "iva_ret": float(iva_ret.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        }
    return None

def sanitize_name(name: str) -> str:
    """
    Removes corporate regime suffixes for CFDI 4.0 strict name validation.
    Example: "INMOBILIARIA DEL PACIFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACIFICO"
    """
    # Regex to match common suffixes, case insensitive
    # Covers: S.A. DE C.V., S.A., S.C., S. DE R.L. DE C.V., etc.
    # We use word boundaries (\b) and end of string ($) to prevent false positives (e.g. "EMPRESA")

    # List of common regimes to strip
    # Note: Order matters. Longer matches should be first if they share substrings,
    # but the loop handles them sequentially.
    regimes = [
        r",?\s*\bS\.?A\.?\s*DE\s*C\.?V\.?$",
        r",?\s*\bS\.?A\.?P\.?I\.?\s*DE\s*C\.?V\.?$",
        r",?\s*\bS\.?\s*DE\s*R\.?L\.?\s*DE\s*C\.?V\.?$",
        r",?\s*\bS\.?A\.?$",
        r",?\s*\bS\.?C\.?$",
        r",?\s*\bS\.?C\.?P\.?$",
        r",?\s*\bA\.?C\.?$",
        r",?\s*\bS\.?A\.?S\.?$"
    ]

    cleaned_name = name.strip()

    for regime in regimes:
        cleaned_name = re.sub(regime, "", cleaned_name, flags=re.IGNORECASE)

    # Remove trailing punctuation and spaces
    cleaned_name = cleaned_name.strip(" .,")

    return cleaned_name

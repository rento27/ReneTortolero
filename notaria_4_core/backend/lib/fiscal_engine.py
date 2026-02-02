import re
from decimal import Decimal, getcontext

# Set precision for fiscal calculations
getcontext().prec = 28

def sanitize_name(name: str) -> str:
    """
    Sanitizes the name for CFDI 4.0 strict validation.
    Removes Regime suffixes like 'S.A. DE C.V.', 'S.C.', etc.
    """
    if not name:
        return ""

    # Normalize to uppercase
    clean_name = name.upper().strip()

    # Remove trailing commas before processing regex
    clean_name = re.sub(r",\s*$", "", clean_name)

    # Common Regimes to strip (Regex pattern)
    # This pattern looks for common endings preceded by space or comma
    # It attempts to be conservative but effective based on the prompt's example.
    patterns = [
        r"\s+S\.?A\.?\s+DE\s+C\.?V\.?$",
        r"\s+S\.?A\.?B\.?\s+DE\s+C\.?V\.?$",
        r"\s+S\.?\s+DE\s+R\.?L\.?\s+DE\s+C\.?V\.?$",
        r"\s+S\.?C\.?$",
        r"\s+S\.?A\.?$",
        r"\s+A\.?C\.?$",
        r",?\s*SOCIEDAD ANONIMA DE CAPITAL VARIABLE$",
        r",?\s*SOCIEDAD CIVIL$"
    ]

    for pattern in patterns:
        clean_name = re.sub(pattern, "", clean_name, flags=re.IGNORECASE)

    # Remove trailing commas again if they were left behind after stripping regime
    clean_name = re.sub(r",\s*$", "", clean_name)

    return clean_name.strip()

def calculate_retentions(subtotal: Decimal, rfc_receptor: str) -> dict:
    """
    Calculates ISR and IVA retentions for Personas Morales.
    Rule: If RFC length is 12, apply retentions.
    """
    # Ensure subtotal is Decimal
    if not isinstance(subtotal, Decimal):
        subtotal = Decimal(str(subtotal))

    results = {
        "is_persona_moral": False,
        "isr_retention": Decimal("0.00"),
        "iva_retention": Decimal("0.00"),
        "total_retention": Decimal("0.00")
    }

    if len(rfc_receptor) == 12:
        results["is_persona_moral"] = True

        # ISR: 10%
        results["isr_retention"] = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"))

        # IVA: 2/3 of VAT (10.666667%)
        # Explicit math: (Subtotal * 0.16) * (2/3) or Subtotal * 0.106667
        # The prompt mentions 10.6667% as the effective rate, but legally it's 2/3 of the transferred tax.
        # Let's calculate it as 10.6667% for direct alignment with the prompt's "The Rule of Two Thirds" section
        # which says "Mathematically, this equals a rate of 10.6667%".

        # Using the prompt's specific rate for precision
        rate = Decimal("0.106667")
        results["iva_retention"] = (subtotal * rate).quantize(Decimal("0.01"))

        results["total_retention"] = results["isr_retention"] + results["iva_retention"]

    return results

def calculate_isai_manzanillo(precio_operacion: Decimal, valor_catastral: Decimal, tasa: Decimal = Decimal("0.03")) -> Decimal:
    """
    Calculates ISAI for Manzanillo.
    Formula: Max(Precio, ValorCatastral) * Tasa
    """
    base_gravable = max(precio_operacion, valor_catastral)
    impuesto = base_gravable * tasa
    return impuesto.quantize(Decimal("0.01"))

def validate_copropiedad(percentages: list[Decimal]) -> bool:
    """
    Validates that the sum of copropiedad percentages is exactly 100.00%.
    Accepts a list of Decimal percentages.
    """
    total = sum(percentages)
    # Using strict comparison as per requirement "Sum(Porcentajes) == 100.00%"
    # We compare against Decimal(100)
    return total == Decimal("100.00")

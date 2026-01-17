import re
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Union, Tuple

def sanitize_name(name: str) -> str:
    """
    Removes corporate regime suffixes from a company name for CFDI 4.0 compliance.
    Example: "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACÍFICO"

    CFDI 4.0 requires the name to match exactly the 'Constancia de Situación Fiscal'
    without the regime.
    """
    if not name:
        return ""

    # Normalize spaces and strip
    cleaned_name = " ".join(name.split()).upper()

    # Common Mexican corporate suffixes (Regimen Societario)
    # This regex attempts to catch variations with/without dots and spaces
    # It anchors to the end of the string ($)
    # Includes: S.A., S.C., S.A.S., S. de R.L., S.A. de C.V., etc.
    regime_pattern = r"\s+(?:S\.?\s*A\.?\s*B\.?\s*DE\s*C\.?\s*V\.?|S\.?\s*A\.?\s*P\.?\s*I\.?\s*DE\s*C\.?\s*V\.?|S\.?\s*A\.?\s*DE\s*C\.?\s*V\.?|S\.?\s*DE\s*R\.?\s*L\.?\s*DE\s*C\.?\s*V\.?|S\.?\s*DE\s*R\.?\s*L\.?|S\.?\s*A\.?\s*S\.?|S\.?\s*A\.?|S\.?\s*C\.?|INC\.?|LTD\.?|A\.?\s*C\.?|I\.?\s*A\.?\s*P\.?)\.?$"

    # Remove the suffix
    cleaned_name = re.sub(regime_pattern, "", cleaned_name, flags=re.IGNORECASE)

    # Remove trailing punctuation (commas often used before SA de CV)
    cleaned_name = cleaned_name.rstrip(".,")

    return cleaned_name

def calculate_retentions(subtotal: Decimal, receiver_rfc: str) -> Dict[str, Decimal]:
    """
    Calculates ISR and IVA retentions based on the receiver's RFC type (Persona Moral).

    Rules:
    - If RFC length is 12 (Persona Moral):
        - ISR Retention: 10%
        - IVA Retention: 2/3 of the VAT (16%), approx 10.6667%
    - If RFC length is 13 (Persona Física): No retentions (usually, dependent on regime but standard for Notaries to PM).
    """
    retentions = {
        "isr_retention": Decimal("0.00"),
        "iva_retention": Decimal("0.00")
    }

    if not receiver_rfc:
        return retentions

    clean_rfc = receiver_rfc.strip().upper()

    # Check for Persona Moral (12 chars)
    if len(clean_rfc) == 12:
        # ISR Retention: 10%
        retentions["isr_retention"] = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # IVA Retention: 2/3 of IVA (16%)
        # Logic: IVA is 16%. Retention is (16% * 2) / 3.
        # Calculation using high precision before rounding
        iva_rate = Decimal("0.16")
        iva_amount = subtotal * iva_rate
        retention_amount = (iva_amount * Decimal("2") / Decimal("3"))

        retentions["iva_retention"] = retention_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return retentions

def calculate_isai(price: Decimal, cadastral_value: Decimal, rate: Decimal) -> Decimal:
    """
    Calculates ISAI (Impuesto Sobre Adquisición de Inmuebles) for Manzanillo.
    Formula: Max(Operation Price, Cadastral Value) * Rate
    """
    base = max(price, cadastral_value)
    isai = base * rate
    return isai.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def validate_copropiedad(percentages: List[Decimal]) -> bool:
    """
    Validates that the sum of copropiedad percentages is exactly 100.00%.
    Returns True if valid, False otherwise.
    """
    total = sum(percentages)
    # We use a small epsilon for float comparison if strictly needed,
    # but with Decimal it should be exact.
    # Requirement: "Strict validation: Sum == 100.00%"
    target = Decimal("100.00")
    return total == target

def validate_zip_code(zip_code: str, state_code: str = None) -> bool:
    """
    Validates zip code format and optionally cross-references with state.

    TODO: Integrate with Firestore/Storage 'c_CodigoPostal' catalog.
    Currently performs format validation.
    """
    if not re.match(r"^\d{5}$", zip_code):
        return False

    # Placeholder for state validation logic
    # Example: Colima (State 06) Zips usually start with 28
    if state_code == "06" and not zip_code.startswith("28"):
        # This is a soft check for now, Manzanillo is 28xxx
        pass

    return True

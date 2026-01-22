import re
from decimal import Decimal, ROUND_HALF_UP

def sanitize_name(name: str) -> str:
    """
    Removes corporate regimes from the name for CFDI 4.0 compliance.
    Example: "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACIFICO"
    Also normalizes unicode characters.
    """
    # Normalize unicode (simple approach for now, can be expanded with unicodedata)
    # Removing common regime suffixes. The regex needs to be robust.
    # We will use a predefined list of common suffixes in Mexico.

    import unicodedata
    name = name.upper().strip()
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')

    # List of common suffixes to remove (simplified list)
    suffixes = [
        r",?\s*S\.?A\.?\s*DE\s*C\.?V\.?",
        r",?\s*S\.?A\.?\s*DE\s*C\.?V\.?",
        r",?\s*S\.?A\.?",
        r",?\s*S\.?C\.?",
        r",?\s*S\.?C\.?\s*DE\s*R\.?L\.?\s*DE\s*C\.?V\.?",
        r",?\s*S\.? DE R\.?L\.? DE C\.?V\.?",
        r",?\s*S\.?A\.?P\.?I\.? DE C\.?V\.?",
        r",?\s*LTD",
        r",?\s*INC",
        r",?\s*S\.?A\.?B\.? DE C\.?V\.?"
    ]

    for suffix in suffixes:
        name = re.sub(suffix + "$", "", name)

    return name.strip()

def calculate_retentions(subtotal: Decimal, rfc_receptor: str) -> dict:
    """
    Calculates ISR and IVA retentions for Personas Morales (RFC length 12).
    ISR: 10%
    IVA: 2/3 of IVA (approx 10.6667%)
    """
    if len(rfc_receptor) == 12:
        # Persona Moral
        isr_retention = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # IVA Retention: 2/3 of the transferred IVA.
        # Assuming standard IVA rate is 16%.
        # So retention is 16% * (2/3) = 10.6666...%
        # The prompt mentions: "Matemáticamente, esto equivale a una tasa del 10.6667%"
        # Let's use the explicit factor mentioned or calculate it.
        # Ideally: (subtotal * 0.16) * (2/3)

        iva_amount = subtotal * Decimal('0.16')
        iva_retention = (iva_amount * Decimal('2') / Decimal('3')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return {
            "isr_retention": isr_retention,
            "iva_retention": iva_retention,
            "is_persona_moral": True
        }

    return {
        "isr_retention": Decimal('0.00'),
        "iva_retention": Decimal('0.00'),
        "is_persona_moral": False
    }

def calculate_isai_manzanillo(price: Decimal, cadastral_value: Decimal, rate: Decimal = Decimal('0.03')) -> Decimal:
    """
    Calculates ISAI for Manzanillo.
    Formula: Max(Price, Cadastral) * Rate
    """
    base = max(price, cadastral_value)
    isai = base * rate
    return isai.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def validate_copropiedad(percentages: list[Decimal]) -> bool:
    """
    Validates that the sum of percentages equals exactly 100.00%.
    """
    total = sum(percentages)
    # Using a small epsilon or exact match since we use Decimal
    return total == Decimal('100.00')

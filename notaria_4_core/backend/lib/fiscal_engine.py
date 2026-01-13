import re
from decimal import Decimal, getcontext

# Set precision for high-accuracy fiscal calculations
getcontext().prec = 28

TASA_ISAI_DEFAULT = Decimal("0.03") # 3% default for Manzanillo

def sanitize_name(name: str) -> str:
    """
    Removes corporate regimes from the name to comply with CFDI 4.0 strict validation.
    Example: "INMOBILIARIA DEL PACIFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACIFICO"
    """
    # Regex to match common suffixes at the end of the string, case insensitive
    # Matches comma optional, space optional, and the regime
    regime_pattern = re.compile(r"[,.]?\s+(S\.?A\.?|S\.?C\.?|S\.?R\.?L\.?|S\.?A\.?B\.?|S\.?A\.?P\.?I\.?|L\.?T\.?D\.?|INC\.?|A\.?C\.?|I\.?A\.?P\.?).*$", re.IGNORECASE)

    clean_name = regime_pattern.sub("", name).strip()
    return clean_name.upper()

def calculate_fiscal_data(rfc_receptor: str, monto_operacion: float, valor_catastral: float):
    """
    Calculates ISAI and Retentions based on fiscal rules.
    """
    monto_op_dec = Decimal(str(monto_operacion))
    valor_cat_dec = Decimal(str(valor_catastral))

    # ISAI Manzanillo: Max(Price, Catastral) * Rate
    base_isai = max(monto_op_dec, valor_cat_dec)
    isai_amount = base_isai * TASA_ISAI_DEFAULT

    retentions = {}

    # Persona Moral Check (RFC length 12)
    if len(rfc_receptor) == 12:
        # Dummy base for fees (honorarios) - in real app this comes from specific line items
        # This is just demonstrating the rate logic
        base_honorarios = Decimal("1000.00") # Example

        # ISR 10%
        isr = base_honorarios * Decimal("0.10")

        # IVA 2/3 (10.6667%)
        # 16% IVA amount
        iva_trasladado = base_honorarios * Decimal("0.16")
        iva_retanido = (iva_trasladado / Decimal("3")) * Decimal("2")

        retentions = {
            "isr_amount": float(round(isr, 2)),
            "iva_retenido_amount": float(round(iva_retanido, 2)),
            "note": "Persona Moral Detected: Applied 10% ISR and 2/3 IVA retention."
        }

    return {
        "isai_calculation": {
            "base": float(base_isai),
            "rate": float(TASA_ISAI_DEFAULT),
            "amount": float(round(isai_amount, 2))
        },
        "retentions": retentions
    }

def validate_copropiedad(percentages: list[Decimal]) -> bool:
    """
    Validates that the sum of copropiedad percentages is exactly 100.00%.
    """
    total = sum(percentages)
    return total == Decimal("100.00")

from decimal import Decimal, getcontext
import re

# Set precision high enough for fiscal calculations
getcontext().prec = 10

def sanitize_name(name: str) -> str:
    """
    Removes corporate regimes like 'S.A. DE C.V.' to comply with CFDI 4.0 strict name validation.
    Also handles trailing punctuation and whitespace.
    """
    # Common corporate suffixes in Mexico
    regex_pattern = r"\s+(S\.?A\.?(\s+DE\s+C\.?V\.?)?|S\.?C\.?|S\.? DE R\.?L\.?(\s+DE\s+C\.?V\.?)?|S\.?A\.?S\.?)$"
    cleaned_name = re.sub(regex_pattern, "", name, flags=re.IGNORECASE)
    return cleaned_name.strip(" .,")

def calculate_isai_manzanillo(precio_operacion: Decimal, valor_catastral: Decimal, tasa: Decimal = Decimal('0.03')) -> Decimal:
    """
    Calculates ISAI for Manzanillo.
    Formula: Max(Price, Cadastral) * Rate
    """
    base_gravable = max(precio_operacion, valor_catastral)
    return base_gravable * tasa

def calculate_retentions_persona_moral(subtotal: Decimal, is_persona_moral: bool) -> dict:
    """
    Calculates ISR and IVA retentions for Personas Morales.
    ISR: 10%
    IVA: 2/3 of IVA Trasladado (16%) -> ~10.6666%
    """
    if not is_persona_moral:
        return {"ret_isr": Decimal(0), "ret_iva": Decimal(0)}

    ret_isr = subtotal * Decimal('0.10')
    # IVA is 16%, Retention is 2/3 of that.
    # Mathematically: Subtotal * 0.16 * (2/3) = Subtotal * 0.106666...
    iva_trasladado = subtotal * Decimal('0.16')
    ret_iva = (iva_trasladado * Decimal('2')) / Decimal('3')

    return {
        "ret_isr": ret_isr,
        "ret_iva": ret_iva
    }

def validate_copropiedad(percentages: list[Decimal]) -> bool:
    """
    Validates that the sum of copropiedad percentages equals exactly 100.00%
    """
    total = sum(percentages)
    return total == Decimal('100.00')

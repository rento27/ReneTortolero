import re
from decimal import Decimal, ROUND_HALF_UP, getcontext

# Set precision for fiscal calculations
getcontext().prec = 50
ROUNDING_MODE = ROUND_HALF_UP

def sanitize_name(name: str) -> str:
    """
    Removes corporate regimes from the name to comply with SAT CFDI 4.0.
    Example: 'INMOBILIARIA DEL PACÍFICO, S.A. DE C.V.' -> 'INMOBILIARIA DEL PACIFICO'
    """
    if not name:
        return ""

    clean_name = name.upper().strip()

    # Replace accents
    replacements = {
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U'
    }
    for char, repl in replacements.items():
        clean_name = clean_name.replace(char, repl)

    # Regex to match common Mexican corporate suffixes at the end of the string
    # We use a non-capturing group for the suffix and anchor to end of string ($)
    suffixes = [
        r"\s+S\.?A\.?\s+DE\s+C\.?V\.?",
        r"\s+S\.?A\.?B\.?\s+DE\s+C\.?V\.?",
        r"\s+S\.?C\.?\s+DE\s+R\.?L\.?\s+DE\s+C\.?V\.?",
        r"\s+S\.?A\.?\s+DE\s+C\.?V\.?\s+S\.?N\.?C\.?",
        r"\s+S\.? DE R\.?L\.? DE C\.?V\.?",
        r"\s+S\.?A\.?P\.?I\.? DE C\.?V\.?",
        r"\s+S\.?A\.?",
        r"\s+S\.?C\.?",
        r"\s+S\.?C\.?P\.?",
        r"\s+A\.?C\.?",
        r"\s+S\.?N\.?C\.?",
        r"\s+S\.?A\.?S\.?"
    ]

    for suffix in suffixes:
        clean_name = re.sub(suffix + r"$", "", clean_name, flags=re.IGNORECASE)

    # Remove trailing punctuation (commas, periods)
    clean_name = re.sub(r"[,\.]+$", "", clean_name).strip()

    return clean_name

def get_retention_rates(rfc: str):
    """
    Determines retention rates based on RFC length.
    RFC length 12 -> Persona Moral -> Retain ISR (10%) and IVA (2/3).
    RFC length 13 -> Persona Fisica -> No retention (usually).
    """
    if not rfc:
        return {"isr": Decimal("0.00"), "iva": Decimal("0.00")}

    clean_rfc = rfc.strip().upper()

    if len(clean_rfc) == 12:
        # Persona Moral
        return {
            "isr": Decimal("0.10"),
            "iva": Decimal("0.106667") # 2/3 of 0.16 approx. The exact logic might be 0.16 * (2/3)
        }
    return {"isr": Decimal("0.00"), "iva": Decimal("0.00")}

def calculate_isai(operation_price: Decimal, cadastral_value: Decimal, rate: Decimal = Decimal("0.03")) -> Decimal:
    """
    Calculates ISAI (Impuesto Sobre Adquisición de Inmuebles) for Manzanillo.
    Formula: Max(Price, Cadastral) * Rate
    """
    base = max(operation_price, cadastral_value)
    return (base * rate).quantize(Decimal("0.01"), rounding=ROUNDING_MODE)

def validate_copropiedad(percentages: list[Decimal]) -> bool:
    """
    Validates that the sum of copropiedad percentages is exactly 100.00%.
    """
    total = sum(percentages)
    return total == Decimal("100.00")

def validate_postal_code_structure(cp: str) -> bool:
    """
    Basic structural validation of the postal code.
    Deep validation against catalog should be done via database lookup.
    """
    return bool(cp and len(cp) == 5 and cp.isdigit())

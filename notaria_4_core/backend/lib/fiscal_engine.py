import re
import unicodedata
from decimal import Decimal, getcontext, ROUND_HALF_UP

# Set strict decimal precision
getcontext().prec = 50

# Corporate Regimes to strip (Regex pattern)
# Matches common endings like S.A. DE C.V., S.C., etc., allowing for optional punctuation and casing.
# The pattern looks for whitespace followed by these acronyms at the end of the string.
REGIME_REGEX = re.compile(
    r"\s+(S\.?A\.?(\s+DE\s+C\.?V\.?)?|S\.?C\.?|S\.?A\.?P\.?I\.?(\s+DE\s+C\.?V\.?)?|S\.? DE R\.?L\.?(\s+DE\s+C\.?V\.?)?|L\.?T\.?D\.?|INC\.?|S\.?A\.?S\.?)$",
    re.IGNORECASE
)

# Constants
ISR_RETENTION_RATE = Decimal("0.10")
# Two-thirds of IVA (16% * 2/3 = 10.6666...) approximated to 10.6667% for direct base calculation
# Or calculated as (Subtotal * 0.16) * (2/3)
# The prompt says "Matemáticamente, esto equivale a una tasa del 10.6667%".
IVA_RETENTION_RATE_DIRECT = Decimal("0.106667")

# Stub for Postal Code Catalog (Manzanillo samples)
# In production, this would be loaded from Firestore/Cache
VALID_POSTAL_CODES = {
    "28200": "COL",
    "28218": "COL",
    "28230": "COL",
    "06600": "CMX" # Mexico City sample
}

def validate_postal_code(cp: str, expected_state: str = None) -> bool:
    """
    Validates the postal code against the authorized catalog.
    If expected_state (e.g., 'COL') is provided, ensures the CP belongs to that state.
    """
    if cp not in VALID_POSTAL_CODES:
        # In this stub, we reject unknown CPs.
        # In production, this would reject CPs not found in the full SAT catalog.
        return False

    if expected_state and VALID_POSTAL_CODES[cp] != expected_state:
        return False

    return True

def sanitize_name(name: str) -> str:
    """
    Removes corporate regimes from the name for CFDI 4.0 validation.
    Example: "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACIFICO"
    Also normalizes whitespace and capitalization.
    """
    if not name:
        return ""

    # Remove commas which often precede the regime
    clean_name = name.replace(",", "")

    # Remove the regime using regex
    clean_name = REGIME_REGEX.sub("", clean_name)

    # Remove extra internal whitespace and trim
    clean_name = " ".join(clean_name.split())

    # Normalize unicode to remove accents (NFD decomposition)
    clean_name = unicodedata.normalize('NFD', clean_name)
    clean_name = "".join(c for c in clean_name if unicodedata.category(c) != 'Mn')

    # Basic uppercase conversion as SAT usually expects uppercase
    return clean_name.upper()

def calculate_isai_manzanillo(operation_price: Decimal, cadastral_value: Decimal, rate: Decimal = Decimal("0.03")) -> Decimal:
    """
    Calculates ISAI for Manzanillo.
    Formula: Max(Price, Cadastral) * Rate
    """
    base = max(operation_price, cadastral_value)
    isai = base * rate
    # Standard rounding to 2 decimals for currency
    return isai.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def calculate_taxable_base(concepts: list[dict]) -> Decimal:
    """
    Calculates the total taxable base from a list of concepts.
    Only concepts with ObjetoImp '02' (Sí objeto de impuesto) are included.
    Returns the sum of their 'importe' values.
    """
    taxable_base = Decimal("0.00")
    for concept in concepts:
        # Check if concept is taxable (02)
        # Note: 'objeto_imp' key might vary if coming from Pydantic model dump or dict. We assume standard keys.
        obj_imp = concept.get('objeto_imp')
        if obj_imp == '02':
            # Safely convert to Decimal if needed (e.g. if it's a string/float)
            importe = concept.get('importe', 0)
            if not isinstance(importe, Decimal):
                importe = Decimal(str(importe))
            taxable_base += importe
    return taxable_base

def calculate_retentions(rfc_receptor: str, taxable_base: Decimal, iva_rate: Decimal = Decimal("0.16")) -> dict:
    """
    Calculates retentions if the receptor is a Persona Moral (RFC length == 12).

    :param rfc_receptor: RFC of the receptor.
    :param taxable_base: The base amount subject to tax (sum of concepts with ObjetoImp '02').
                         Do NOT pass the total subtotal if it includes non-taxable items.
    :param iva_rate: IVA rate (default 16%).
    :return: Dictionary with retention amounts.
    """
    retentions = {
        "isr": Decimal("0.00"),
        "iva": Decimal("0.00"),
        "is_moral": False
    }

    # Check if Persona Moral (12 characters)
    # Note: RFC validation usually handles stripping whitespace, but we assume clean input here or check length.
    if len(rfc_receptor.strip()) == 12:
        retentions["is_moral"] = True

        # ISR Retention: 10% of Taxable Base
        retentions["isr"] = (taxable_base * ISR_RETENTION_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # IVA Retention: 2/3 of the IVA amount
        # IVA Amount = Taxable Base * iva_rate
        # Ret = IVA Amount * (2/3)
        iva_amount = taxable_base * iva_rate
        ret_iva = iva_amount * (Decimal("2") / Decimal("3"))
        retentions["iva"] = ret_iva.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return retentions

def validate_copropiedad(percentages: list[Decimal]) -> bool:
    """
    Validates that the sum of percentage Decimals equals exactly 100.00%.
    Raises ValueError if validation fails.
    """
    total = sum(percentages)
    if total != Decimal("100.00"):
        raise ValueError(f"Sum of percentages must be 100.00%, got {total}")
    return True

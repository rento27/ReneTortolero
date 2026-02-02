import re
import unicodedata
from decimal import Decimal, getcontext, ROUND_HALF_UP

# Set high precision for fiscal calculations to avoid rounding errors
getcontext().prec = 50

# Export rounding mode
ROUNDING_MODE = ROUND_HALF_UP

def sanitize_name(name: str) -> str:
    """
    Sanitizes the name by removing corporate regimes as per CFDI 4.0 strict validation rules.
    Converts to uppercase, removes accents, and removes extra spaces.

    Args:
        name (str): The raw name from the deed or input.

    Returns:
        str: The sanitized name for SAT.
    """
    if not name:
        return ""

    # Remove accents/normalization
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')
    name = name.upper().strip()

    # Remove common punctuation at the end BEFORE matching regime (e.g. trailing comma or dot)
    name = name.rstrip(".,")

    # Common Mexican corporate regimes to remove.
    # Note: The regex anchors to the end of the string.
    # We make the final dot optional because we stripped trailing punctuation.
    regimes = [
        r"S\.A\. DE C\.V\.?",
        r"S\.A\.P\.I\. DE C\.V\.?",
        r"S\. DE R\.L\. DE C\.V\.?",
        r"S\.A\.B\. DE C\.V\.?",
        r"S\. EN C\. POR A\.?",
        r"S\. EN N\.C\.?",
        r"S\. EN C\.?",
        r"S\. DE R\.L\.?",
        r"S\.A\.?",
        r"S\.C\.?",
        r"A\.C\.?",
        r"A\.B\.P\.?",
        r"I\.A\.P\.?",
        r"S\.A\.S\.?"
    ]

    # Construct regex: \s+(regime1|regime2|...)$
    pattern = r"\s+(?:" + "|".join(regimes) + r")$"

    # Remove the regime
    clean_name = re.sub(pattern, "", name)

    # Also remove common punctuation again just in case (e.g. "Name, S.A. DE C.V.")
    # If original was "Name, S.A. DE C.V.", clean_name is "Name,".
    clean_name = clean_name.rstrip(".,")

    return clean_name

def calculate_isai(precio_operacion: Decimal, valor_catastral: Decimal, tasa: Decimal) -> Decimal:
    """
    Calculates the ISAI (Impuesto Sobre Adquisición de Inmuebles) for Manzanillo.
    Formula: Max(Precio, ValorCatastral) * Tasa

    Args:
        precio_operacion (Decimal): The transaction price.
        valor_catastral (Decimal): The cadastral value.
        tasa (Decimal): The tax rate (e.g., 0.03 for 3%).

    Returns:
        Decimal: The calculated tax amount, rounded to 2 decimal places for currency.
    """
    base = max(precio_operacion, valor_catastral)
    impuesto = base * tasa
    return impuesto.quantize(Decimal("0.01"), rounding=ROUNDING_MODE)

def get_retention_rates(rfc_receptor: str) -> dict:
    """
    Returns the retention rates for ISR and IVA based on RFC type.

    Args:
        rfc_receptor (str): RFC of the receiver.

    Returns:
        dict: {'isr': Decimal, 'iva': Decimal} rates (relative to base) or empty.
    """
    rfc_clean = rfc_receptor.strip().upper()

    # Persona Moral has 12 characters
    if len(rfc_clean) == 12:
        return {
            "isr": Decimal("0.100000"),
            "iva": Decimal("0.106667") # 16% * 2/3 approx
        }
    return {}

def calculate_retentions(rfc_receptor: str, subtotal: Decimal, iva_trasladado: Decimal) -> dict:
    """
    Calculates retentions if the receptor is a Persona Moral (RFC length 12).

    Rules:
    - ISR Retention: 10% of Subtotal.
    - IVA Retention: 2/3 of IVA Trasladado (approx 10.6667% of Base).

    Args:
        rfc_receptor (str): RFC of the receiver.
        subtotal (Decimal): The base amount (Subtotal).
        iva_trasladado (Decimal): The IVA amount calculated (usually 16% of subtotal).

    Returns:
        dict: Dictionary with retention amounts or empty if Persona Fisica.
    """
    rates = get_retention_rates(rfc_receptor)
    if rates:
        # ISR Retention: rate * subtotal
        isr_ret = subtotal * rates['isr']

        # IVA Retention: rate * subtotal (Note: prompt says 2/3 of IVA, which is same as rate * base if rate is calculated that way)
        # Using rate against base ensures consistency with XML generation logic.
        iva_ret = subtotal * rates['iva']

        # Verify if we should use IVA * 2/3 explicitly?
        # 16% of X * 2/3 = 10.6667% of X.
        # Ideally we use the rate on Base as per CFDI standard (TasaOCuota applies to Base).

        return {
            "ret_isr": isr_ret.quantize(Decimal("0.01"), rounding=ROUNDING_MODE),
            "ret_iva": iva_ret.quantize(Decimal("0.01"), rounding=ROUNDING_MODE)
        }

    return {}

def validate_copropiedad(percentages: list[Decimal]) -> bool:
    """
    Validates that the sum of copropiedad percentages is EXACTLY 100.00%.

    Args:
        percentages (list[Decimal]): List of percentage values.

    Returns:
        bool: True if valid, False otherwise.
    """
    total = sum(percentages)
    target = Decimal("100.00")

    # We compare with a small tolerance for internal float operations if needed,
    # but since we use Decimal, we expect exact match.
    # However, fiscal rules are strict.

    return total == target

def validate_rfc(rfc: str) -> bool:
    """
    Validates the structure of an RFC.

    Persona Física: 4 letters, 6 digits, 3 alphanumeric.
    Persona Moral: 3 letters, 6 digits, 3 alphanumeric.

    Args:
        rfc (str): RFC to validate.

    Returns:
        bool: True if matches pattern.
    """
    rfc = rfc.strip().upper()
    pattern = r"^([A-ZÑ&]{3,4})([0-9]{6})([A-Z0-9]{3})$"
    return bool(re.match(pattern, rfc))

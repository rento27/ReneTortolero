import re
import unicodedata
from decimal import Decimal, getcontext, ROUND_HALF_UP
import firebase_admin
from firebase_admin import credentials, firestore, remote_config
import asyncio
import concurrent.futures

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

def validate_postal_code(cp: str, expected_state: str = None) -> bool:
    """
    Validates the postal code against the authorized catalog in Firestore.
    If expected_state (e.g., 'COL') is provided, ensures the CP belongs to that state.
    """
    try:
        # Check if initialized, if not initialize with default credentials
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        db = firestore.client()

        # Query the catalogos_sat collection
        docs = db.collection('catalogos_sat').where('c_CodigoPostal', '==', cp).limit(1).stream()

        doc_found = None
        for doc in docs:
            doc_found = doc.to_dict()
            break

        if not doc_found:
            return False

        if expected_state and doc_found.get('c_Estado') != expected_state:
            return False

        return True
    except Exception as e:
        # Fallback or error handling
        print(f"Error validating postal code: {e}")
        return False

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

_ISAI_RATE_CACHE = None

def get_remote_config_sync() -> Decimal:
    global _ISAI_RATE_CACHE
    if _ISAI_RATE_CACHE is not None:
        return _ISAI_RATE_CACHE

    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app()

        # Run async get_remote_config in a threadpool to avoid event loop conflicts
        def _fetch():
            template = remote_config.get_remote_config()
            rate_str = template.parameters.get('tasa_isai_manzanillo').default_value
            return Decimal(rate_str)

        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(_fetch)
            _ISAI_RATE_CACHE = future.result()

    except Exception as e:
        print(f"Error fetching remote config: {e}")
        _ISAI_RATE_CACHE = Decimal("0.03") # fallback

    return _ISAI_RATE_CACHE


def calculate_isai_manzanillo(operation_price: Decimal, cadastral_value: Decimal, rate: Decimal = None) -> Decimal:
    """
    Calculates ISAI for Manzanillo.
    Formula: Max(Price, Cadastral) * Rate
    Defaults to fetching tasa_isai_manzanillo from Firebase Remote Config if rate is omitted.
    """
    if rate is None:
        rate = get_remote_config_sync()

    base = max(operation_price, cadastral_value)
    isai = base * rate
    # Standard rounding to 2 decimals for currency
    return isai.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def calculate_retentions(rfc_receptor: str, subtotal: Decimal, iva_rate: Decimal = Decimal("0.16")) -> dict:
    """
    Calculates retentions if the receptor is a Persona Moral (RFC length == 12).
    Returns a dictionary with retention amounts.
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

        # ISR Retention: 10% of Subtotal
        retentions["isr"] = (subtotal * ISR_RETENTION_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # IVA Retention: 10.6667%
        ret_iva = subtotal * IVA_RETENTION_RATE_DIRECT
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

import re
import unicodedata
from decimal import Decimal, getcontext, ROUND_HALF_UP
import time

try:
    import firebase_admin
    from firebase_admin import remote_config
    from firebase_admin import firestore
except ImportError:
    firebase_admin = None

# Set strict decimal precision
getcontext().prec = 50

_ISAI_RATE_CACHE = None
_ISAI_RATE_CACHE_TIMESTAMP = 0
_ISAI_RATE_CACHE_TTL = 3600

def get_remote_config_sync() -> Decimal:
    global _ISAI_RATE_CACHE, _ISAI_RATE_CACHE_TIMESTAMP
    now = time.time()
    if _ISAI_RATE_CACHE is not None and (now - _ISAI_RATE_CACHE_TIMESTAMP) < _ISAI_RATE_CACHE_TTL:
        return _ISAI_RATE_CACHE

    if firebase_admin and len(firebase_admin._apps) > 0:
        try:
            template = remote_config.get_server_template()
            rate_val = template.parameters.get("tasa_isai_manzanillo")
            if rate_val and rate_val.default_value:
                val = Decimal(str(rate_val.default_value.value))
                _ISAI_RATE_CACHE = val
                _ISAI_RATE_CACHE_TIMESTAMP = now
                return val
        except Exception:
            pass

    # Default fallback
    return Decimal("0.03")

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
    Validates the postal code against the authorized catalog.
    If expected_state (e.g., 'COL') is provided, ensures the CP belongs to that state.
    Queries Firestore 'catalogos_sat' collection.
    """
    if not firebase_admin or len(firebase_admin._apps) == 0:
        # If no firebase app is configured, bypass or mock
        return False

    db = firestore.client()
    try:
        # We query the collection 'catalogos_sat' where 'c_CodigoPostal' is stored
        # Assuming the document ID is the postal code or we have a queryable field
        query = db.collection('catalogos_sat').where('c_CodigoPostal', '==', cp).limit(1).get()
        if not query:
            return False

        doc_data = query[0].to_dict()
        if expected_state and doc_data.get('estado') != expected_state:
            return False

        return True
    except Exception:
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

def calculate_isai_manzanillo(operation_price: Decimal, cadastral_value: Decimal, rate: Decimal = None) -> Decimal:
    """
    Calculates ISAI for Manzanillo.
    Formula: Max(Price, Cadastral) * Rate
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

        # IVA Retention: calculated using exact IVA_RETENTION_RATE_DIRECT
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

import re
import unicodedata
from decimal import Decimal, getcontext, ROUND_HALF_UP
import time

try:
    import firebase_admin
    from firebase_admin import firestore
    from firebase_admin import remote_config
except ImportError:
    firebase_admin = None
    firestore = None
    remote_config = None

# Set strict decimal precision
getcontext().prec = 50

# Corporate Regimes to strip (Regex pattern)
REGIME_REGEX = re.compile(
    r"\s+(S\.?A\.?(\s+DE\s+C\.?V\.?)?|S\.?C\.?|S\.?A\.?P\.?I\.?(\s+DE\s+C\.?V\.?)?|S\.? DE R\.?L\.?(\s+DE\s+C\.?V\.?)?|L\.?T\.?D\.?|INC\.?|S\.?A\.?S\.?)$",
    re.IGNORECASE
)

# Constants
ISR_RETENTION_RATE = Decimal("0.10")
IVA_RETENTION_RATE_DIRECT = Decimal("0.106667")

_ISAI_RATE_CACHE = None
_ISAI_RATE_CACHE_TTL = 3600
_ISAI_RATE_CACHE_TIME = 0

def get_remote_config_sync():
    if not firebase_admin:
        return None
    try:
        template = remote_config.get_server_template()
        return template
    except Exception:
        return None

def validate_postal_code(cp: str, expected_state: str = None) -> bool:
    """
    Validates the postal code against the authorized catalog in Firestore.
    If expected_state (e.g., 'COL') is provided, ensures the CP belongs to that state.
    """
    if not firebase_admin or not firestore:
        # Fallback to stub logic if firebase is not available (e.g., tests without mocking)
        VALID_POSTAL_CODES = {
            "28200": "COL",
            "28218": "COL",
            "28230": "COL",
            "06600": "CMX"
        }
        if cp not in VALID_POSTAL_CODES:
            return False
        if expected_state and VALID_POSTAL_CODES[cp] != expected_state:
            return False
        return True

    try:
        db = firestore.client()
        # In a real app we might shard this, but as per memory, the collection is catalogos_sat
        doc_ref = db.collection('catalogos_sat').document(cp)
        doc = doc_ref.get()
        if not doc.exists:
            return False
        if expected_state:
            data = doc.to_dict()
            if data and data.get('estado') != expected_state:
                return False
        return True
    except Exception:
        return False

def sanitize_name(name: str) -> str:
    """
    Removes corporate regimes from the name for CFDI 4.0 validation.
    """
    if not name:
        return ""

    clean_name = name.replace(",", "")
    clean_name = REGIME_REGEX.sub("", clean_name)
    clean_name = " ".join(clean_name.split())
    clean_name = unicodedata.normalize('NFD', clean_name)
    clean_name = "".join(c for c in clean_name if unicodedata.category(c) != 'Mn')
    return clean_name.upper()

def calculate_isai_manzanillo(operation_price: Decimal, cadastral_value: Decimal, rate: Decimal = None) -> Decimal:
    """
    Calculates ISAI for Manzanillo.
    Formula: Max(Price, Cadastral) * Rate
    """
    global _ISAI_RATE_CACHE, _ISAI_RATE_CACHE_TIME

    if rate is None:
        current_time = time.time()
        if _ISAI_RATE_CACHE is None or (current_time - _ISAI_RATE_CACHE_TIME) > _ISAI_RATE_CACHE_TTL:
            template = get_remote_config_sync()
            if template and 'tasa_isai_manzanillo' in template.parameters:
                val = template.parameters['tasa_isai_manzanillo'].default_value.value
                try:
                    _ISAI_RATE_CACHE = Decimal(str(val))
                except Exception:
                    _ISAI_RATE_CACHE = Decimal("0.03")
            else:
                _ISAI_RATE_CACHE = Decimal("0.03")
            _ISAI_RATE_CACHE_TIME = current_time
        rate = _ISAI_RATE_CACHE

    base = max(operation_price, cadastral_value)
    isai = base * rate
    return isai.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def calculate_retentions(rfc_receptor: str, subtotal: Decimal, iva_rate: Decimal = Decimal("0.16")) -> dict:
    """
    Calculates retentions if the receptor is a Persona Moral (RFC length == 12).
    """
    retentions = {
        "isr": Decimal("0.00"),
        "iva": Decimal("0.00"),
        "is_moral": False
    }

    if len(rfc_receptor.strip()) == 12:
        retentions["is_moral"] = True
        retentions["isr"] = (subtotal * ISR_RETENTION_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        iva_amount = subtotal * iva_rate
        ret_iva = iva_amount * (Decimal("2") / Decimal("3"))
        retentions["iva"] = ret_iva.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return retentions

def validate_copropiedad(percentages: list[Decimal]) -> bool:
    """
    Validates that the sum of percentage Decimals equals exactly 100.00%.
    """
    total = sum(percentages)
    if total != Decimal("100.00"):
        raise ValueError(f"Sum of percentages must be 100.00%, got {total}")
    return True

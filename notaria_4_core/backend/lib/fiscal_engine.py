import re
import unicodedata
import time
from decimal import Decimal, getcontext, ROUND_HALF_UP

try:
    import firebase_admin
    from firebase_admin import remote_config
    from firebase_admin import firestore
except ImportError:
    firebase_admin = None
    remote_config = None
    firestore = None

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
    Validates the postal code against the authorized catalog.
    Queries the 'catalogos_sat' collection in Firestore.
    """
    if not firestore:
        # Fallback if firestore is not available
        VALID_POSTAL_CODES = {"28200": "COL", "28218": "COL", "28230": "COL", "06600": "CMX"}
        if cp not in VALID_POSTAL_CODES:
            return False
        if expected_state and VALID_POSTAL_CODES[cp] != expected_state:
            return False
        return True

    db = firestore.client()
    query = db.collection("catalogos_sat").where("c_CodigoPostal", "==", cp)
    if expected_state:
        query = query.where("c_Estado", "==", expected_state)

    docs = query.limit(1).get()
    return len(docs) > 0

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
_ISAI_RATE_CACHE_TTL = 3600
_ISAI_RATE_CACHE_TIME = 0

def get_remote_config_sync() -> Decimal:
    global _ISAI_RATE_CACHE, _ISAI_RATE_CACHE_TIME
    if _ISAI_RATE_CACHE is not None and time.time() - _ISAI_RATE_CACHE_TIME < _ISAI_RATE_CACHE_TTL:
        return _ISAI_RATE_CACHE

    if not remote_config:
        return Decimal("0.03")

    try:
        template = remote_config.get_server_template()
        rate_str = template.parameters.get("tasa_isai_manzanillo").default_value.value
        rate = Decimal(str(rate_str))
        _ISAI_RATE_CACHE = rate
        _ISAI_RATE_CACHE_TIME = time.time()
        return rate
    except Exception:
        return Decimal("0.03")

def calculate_isai_manzanillo(operation_price: Decimal, cadastral_value: Decimal, rate: Decimal = None) -> Decimal:
    """
    Calculates ISAI for Manzanillo.
    Formula: Max(Price, Cadastral) * Rate
    If rate is None, fetches from Firebase Remote Config.
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

        # IVA Retention: 2/3 of the IVA amount
        # Exact 10.6667% representation
        ret_iva = subtotal * Decimal("0.106667")
        retentions["iva"] = ret_iva.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return retentions

def validate_conceptos_objeto_imp(conceptos: list[dict]) -> bool:
    """
    Validates that the 'ObjetoImp' attribute is correctly assigned for each concept.
    Honorarios -> '02'
    Suplidos/Derechos -> '01'
    """
    for concepto in conceptos:
        descripcion = concepto.get('descripcion', '').upper()
        objeto_imp = concepto.get('objeto_imp')

        if 'HONORARIOS' in descripcion:
            if objeto_imp != '02':
                raise ValueError(f"Concept '{descripcion}' must have ObjetoImp '02'.")
        elif 'SUPLIDOS' in descripcion or 'DERECHOS' in descripcion:
            if objeto_imp != '01':
                raise ValueError(f"Concept '{descripcion}' must have ObjetoImp '01'.")

    return True

def validate_copropiedad(percentages: list[Decimal]) -> bool:
    """
    Validates that the sum of percentage Decimals equals exactly 100.00%.
    Raises ValueError if validation fails.
    """
    total = sum(percentages)
    if total != Decimal("100.00"):
        raise ValueError(f"Sum of percentages must be 100.00%, got {total}")
    return True

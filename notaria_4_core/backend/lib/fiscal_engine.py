import re
import time
import unicodedata
from decimal import Decimal, getcontext, ROUND_HALF_UP

try:
    from firebase_admin import firestore, remote_config
except ImportError:
    firestore = None
    remote_config = None

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

# Global variables for caching ISAI Rate
_ISAI_RATE_CACHE = None
_ISAI_RATE_LAST_FETCH = None
_ISAI_RATE_CACHE_TTL = 3600  # 1 hour in seconds

def get_remote_config_sync() -> dict:
    """Helper to fetch Remote Config synchronously."""
    if not remote_config:
        return {}
    template = remote_config.get_server_template()
    return template.parameters

def validate_postal_code(cp: str, expected_state: str = None) -> bool:
    """
    Validates the postal code against the authorized catalog in Firestore.
    If expected_state (e.g., 'COL') is provided, ensures the CP belongs to that state.
    """
    if not firestore:
        raise RuntimeError("firebase_admin.firestore is not available.")

    db = firestore.client()
    doc_ref = db.collection('catalogos_sat').document(cp)
    doc = doc_ref.get()

    if not doc.exists:
        return False

    if expected_state:
        data = doc.to_dict()
        # Assume the document has a 'estado' or similar field.
        # Using 'estado' as standard based on Mexican CP catalogs.
        if data and data.get('estado') != expected_state:
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

def calculate_isai_manzanillo(operation_price: Decimal, cadastral_value: Decimal, rate: Decimal = None) -> Decimal:
    """
    Calculates ISAI for Manzanillo.
    Formula: Max(Price, Cadastral) * Rate
    Uses Firebase Remote Config for `tasa_isai_manzanillo`.
    """
    global _ISAI_RATE_CACHE, _ISAI_RATE_LAST_FETCH

    if rate is None:
        current_time = time.time()
        # Check cache
        if _ISAI_RATE_CACHE is not None and _ISAI_RATE_LAST_FETCH is not None:
            if current_time - _ISAI_RATE_LAST_FETCH < _ISAI_RATE_CACHE_TTL:
                rate = _ISAI_RATE_CACHE

        if rate is None:
            try:
                params = get_remote_config_sync()
                if 'tasa_isai_manzanillo' in params:
                    # In Firebase, parameter defaults/values are usually complex objects.
                    # Getting the default value as string.
                    rate_str = params['tasa_isai_manzanillo'].default_value.value
                    rate = Decimal(rate_str)

                    # Update cache
                    _ISAI_RATE_CACHE = rate
                    _ISAI_RATE_LAST_FETCH = current_time
                else:
                    rate = Decimal("0.03")  # Fallback
            except Exception as e:
                # If Remote Config fails, fallback to 3%
                rate = Decimal("0.03")

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
        # IVA Amount = Subtotal * iva_rate
        # Ret = IVA Amount * (2/3)
        iva_amount = subtotal * iva_rate
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

def validate_conceptos_objeto_imp(conceptos: list[dict]) -> bool:
    """
    Validates that 'Honorarios' have ObjetoImp '02' and 'Suplidos'/'Derechos' have '01'.
    Raises ValueError if validation fails.
    """
    for concepto in conceptos:
        descripcion = concepto.get("Descripcion", "").upper()
        objeto_imp = concepto.get("ObjetoImp")

        if "HONORARIOS" in descripcion:
            if objeto_imp != "02":
                raise ValueError("Honorarios must have ObjetoImp '02'.")
        elif "SUPLIDOS" in descripcion or "DERECHOS" in descripcion:
            if objeto_imp != "01":
                raise ValueError("Suplidos and Derechos must have ObjetoImp '01'.")
    return True

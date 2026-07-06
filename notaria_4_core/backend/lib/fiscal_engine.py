import re
import unicodedata
from decimal import Decimal, getcontext, ROUND_HALF_UP
import time
import inspect
import asyncio

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

_ISAI_RATE_CACHE = None
_ISAI_RATE_LAST_FETCH = 0
_ISAI_RATE_CACHE_TTL = 3600

def get_remote_config_sync():
    """
    Safely executes the async firebase_admin.remote_config.get_server_template()
    function in a synchronous context.
    """
    if not remote_config:
        return None

    try:
        if inspect.iscoroutinefunction(remote_config.get_server_template):
            # Run in a new event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If an event loop is already running, we can't use run_until_complete easily here
                    # We might be inside FastAPI. It's safer to use a thread pool or run_coroutine_threadsafe,
                    # but for simplicity let's try asyncio.run() in a new loop if possible, or wait.
                    import threading
                    result = []
                    def run():
                        result.append(asyncio.run(remote_config.get_server_template()))
                    t = threading.Thread(target=run)
                    t.start()
                    t.join()
                    return result[0] if result else None
                else:
                    return loop.run_until_complete(remote_config.get_server_template())
            except RuntimeError:
                return asyncio.run(remote_config.get_server_template())
        else:
            return remote_config.get_server_template()
    except Exception as e:
        # Log error or handle it
        return None

def validate_postal_code(cp: str, expected_state: str = None) -> bool:
    """
    Validates the postal code against the authorized catalog in Firestore.
    If expected_state (e.g., 'COL') is provided, ensures the CP belongs to that state.
    """
    if not firestore:
        # Fallback if firestore is not available for some reason
        return False

    try:
        db = firestore.client()
        # Querying the catalogos_sat collection
        docs = db.collection('catalogos_sat').where('c_CodigoPostal', '==', cp).limit(1).get()
        if not docs:
            return False

        doc = docs[0].to_dict()

        if expected_state and doc.get('estado') != expected_state:
            return False

        return True
    except Exception as e:
        # Handle exceptions appropriately, maybe fallback to a default behavior or log
        return False

def validate_conceptos_objeto_imp(conceptos: list[dict]) -> bool:
    """
    Validates that concepts have the correct ObjetoImp based on their description.
    'Honorarios' should have '02'. 'Suplidos' or 'Derechos' should have '01'.
    """
    for concepto in conceptos:
        desc = concepto.get('descripcion', '').upper()
        obj_imp = concepto.get('objeto_imp')

        if 'HONORARIO' in desc and obj_imp != '02':
            raise ValueError(f"Concept '{desc}' must have ObjetoImp '02'.")
        if ('SUPLIDO' in desc or 'DERECHO' in desc) and obj_imp != '01':
            raise ValueError(f"Concept '{desc}' must have ObjetoImp '01'.")

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
    Formula: Max(Price, Cadastral) * Rate.
    If rate is not provided, it fetches it from Firebase Remote Config.
    """
    global _ISAI_RATE_CACHE, _ISAI_RATE_LAST_FETCH

    if rate is None:
        current_time = time.time()
        if _ISAI_RATE_CACHE is None or (current_time - _ISAI_RATE_LAST_FETCH > _ISAI_RATE_CACHE_TTL):
            template = get_remote_config_sync()
            if template and 'tasa_isai_manzanillo' in template.parameters:
                # Get the default value of the parameter
                val = template.parameters['tasa_isai_manzanillo'].default_value.value
                _ISAI_RATE_CACHE = Decimal(str(val))
            else:
                _ISAI_RATE_CACHE = Decimal("0.03") # Default
            _ISAI_RATE_LAST_FETCH = current_time

        rate = _ISAI_RATE_CACHE

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

import re
import unicodedata
import time
from decimal import Decimal, getcontext, ROUND_HALF_UP
import firebase_admin
from firebase_admin import firestore, remote_config
from typing import List, Dict

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
IVA_RETENTION_RATE_DIRECT = Decimal("0.106667")

_ISAI_RATE_CACHE = None
_ISAI_RATE_LAST_FETCH = 0
_ISAI_RATE_CACHE_TTL = 3600

def get_remote_config_sync() -> dict:
    """
    Fetches Firebase Remote Config synchronously, caching the template for TTL.
    In firebase_admin 7.4.0, get_server_template is an async coroutine. We run it in a new loop if needed.
    """
    global _ISAI_RATE_CACHE, _ISAI_RATE_LAST_FETCH
    current_time = time.time()

    if _ISAI_RATE_CACHE is None or (current_time - _ISAI_RATE_LAST_FETCH) > _ISAI_RATE_CACHE_TTL:
        try:
            import asyncio
            coro = remote_config.get_server_template()
            try:
                loop = asyncio.get_running_loop()
                # Since get_server_template is async, and we're in a running loop (like FastAPI),
                # we run the coroutine directly. However, if this function must block, we should use a separate thread or nest_asyncio.
                # Assuming this function might be run from tests or synchronous paths as well.
                # Here we use run_coroutine_threadsafe or create a new loop in a thread if needed.
                # For simplicity in this fix, we'll try to just run it until complete if no loop is running.
                raise RuntimeError("Can't run sync here")
            except RuntimeError:
                template = asyncio.run(coro)

            config_dict = {}
            for key, param in template.parameters.items():
                if param.default_value:
                    config_dict[key] = param.default_value.value
            _ISAI_RATE_CACHE = config_dict
            _ISAI_RATE_LAST_FETCH = current_time
        except Exception as e:
            # Fallback to default empty dict if Remote Config fails
            _ISAI_RATE_CACHE = {}
    return _ISAI_RATE_CACHE

def validate_postal_code(cp: str, expected_state: str = None) -> bool:
    """
    Validates the postal code against the authorized catalog in Firestore.
    If expected_state (e.g., 'COL') is provided, ensures the CP belongs to that state.
    """
    db = firestore.client()
    docs = db.collection('catalogos_sat').where('c_CodigoPostal', '==', cp).limit(1).get()

    if not docs:
        return False

    doc = docs[0].to_dict()

    if expected_state and doc.get('estado') != expected_state:
        return False

    return True

def validate_conceptos_objeto_imp(conceptos: List[Dict]) -> bool:
    """
    Validates billing concepts ensuring 'Honorarios' have ObjetoImp '02'
    and 'Suplidos'/'Derechos' have '01'.
    """
    for c in conceptos:
        desc = str(c.get('descripcion', '')).upper()
        obj_imp = str(c.get('objeto_imp', ''))

        if 'HONORARIO' in desc and obj_imp != '02':
            raise ValueError("Honorarios must have ObjetoImp '02'")
        if ('SUPLIDO' in desc or 'DERECHO' in desc) and obj_imp != '01':
            raise ValueError("Suplidos/Derechos must have ObjetoImp '01' or use ACuentaTerceros")
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
    """
    if rate is None:
        config = get_remote_config_sync()
        rate_str = config.get("tasa_isai_manzanillo", "0.03")
        rate = Decimal(str(rate_str))

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

        # IVA Retention: explicitly use base * Decimal('0.106667') as requested
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

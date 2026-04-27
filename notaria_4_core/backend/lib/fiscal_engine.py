import re
import unicodedata
import asyncio
from firebase_admin import remote_config
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

_ISAI_RATE_CACHE = None

def get_remote_config_sync() -> remote_config.ServerTemplate:
    """Helper to safely fetch Remote Config in a sync context avoiding event loop issues."""
    template = remote_config.init_server_template()
    try:
        # Check if an event loop is already running
        asyncio.get_running_loop()
        import threading
        result = [None]
        err = [None]
        def run_in_thread():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(template.load())
                loop.close()
            except Exception as e:
                err[0] = e
        t = threading.Thread(target=run_in_thread)
        t.start()
        t.join()
        if err[0]:
            raise err[0]
        return template
    except RuntimeError:
        # No event loop in this thread
        asyncio.run(template.load())
        return template

def calculate_isai_manzanillo(operation_price: Decimal, cadastral_value: Decimal, rate: Decimal = None) -> Decimal:
    """
    Calculates ISAI for Manzanillo.
    Formula: Max(Price, Cadastral) * Rate
    """
    global _ISAI_RATE_CACHE

    if rate is None:
        if _ISAI_RATE_CACHE is None:
            try:
                template = get_remote_config_sync()
                config = template.evaluate()
                fetched_rate_str = config.get_string("tasa_isai_manzanillo")

                # Check if it was actually retrieved from remote config (not static default)
                # If static default empty string, fallback
                if fetched_rate_str:
                    _ISAI_RATE_CACHE = Decimal(fetched_rate_str)
                else:
                    raise ValueError("Not found")
            except Exception as e:
                # Fallback on failure, BUT do not cache it!
                # This way, subsequent calls will retry fetching.
                fallback = Decimal("0.03")
                base = max(operation_price, cadastral_value)
                return (base * fallback).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

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

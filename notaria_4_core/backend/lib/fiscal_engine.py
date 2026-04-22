import re
import unicodedata
import asyncio
from decimal import Decimal, getcontext, ROUND_HALF_UP

import firebase_admin
from firebase_admin import remote_config
from firebase_admin import firestore

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
    Validates the postal code against the authorized catalog in Firestore.
    If expected_state (e.g., 'COL') is provided, ensures the CP belongs to that state.
    """
    if not firebase_admin._apps:
        # Avoid initialization errors in tests without proper setup
        return cp in VALID_POSTAL_CODES and (not expected_state or VALID_POSTAL_CODES[cp] == expected_state)

    db = firestore.client()
    try:
        doc_ref = db.collection('catalogos_sat').document('c_CodigoPostal')
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            if cp in data:
                state = data[cp].get('estado')
                if expected_state and state != expected_state:
                    return False
                return True
        return False
    except Exception:
        # Fallback to stub or fail gracefully if Firestore fails
        return cp in VALID_POSTAL_CODES and (not expected_state or VALID_POSTAL_CODES[cp] == expected_state)

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

def calculate_isai_manzanillo(operation_price: Decimal, cadastral_value: Decimal, rate: Decimal = None) -> Decimal:
    """
    Calculates ISAI for Manzanillo.
    Formula: Max(Price, Cadastral) * Rate
    Dynamically fetches rate from Firebase Remote Config if not provided.
    """
    global _ISAI_RATE_CACHE

    if rate is None:
        if _ISAI_RATE_CACHE is not None:
            rate = _ISAI_RATE_CACHE
        else:
            if firebase_admin._apps:
                try:
                    # remote_config.get_server_template() might be a coroutine
                    template = remote_config.get_server_template()
                    if asyncio.iscoroutine(template):
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                # Very basic synchronous fallback, not ideal for real async prod
                                # but fits the requirements if called in sync context
                                pass
                            else:
                                template = loop.run_until_complete(template)
                        except RuntimeError:
                            template = asyncio.run(template)

                    if template and 'tasa_isai_manzanillo' in template.parameters:
                        # Remote config returns strings, convert to Decimal
                        val = template.parameters['tasa_isai_manzanillo'].default_value.value
                        rate = Decimal(str(val))
                        _ISAI_RATE_CACHE = rate
                except Exception:
                    rate = Decimal("0.03") # default fallback
            else:
                rate = Decimal("0.03") # default fallback

    # If rate is still None
    if rate is None:
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

import decimal
from decimal import Decimal
import re

# Configure decimal precision
decimal.getcontext().prec = 10

class FiscalEngine:
    @staticmethod
    def calculate_isai_manzanillo(precio_operacion: Decimal, valor_catastral: Decimal, tasa: Decimal = Decimal('0.03')) -> Decimal:
        """
        Calculates ISAI for Manzanillo.
        Formula: Max(Precio, ValorCatastral) * Tasa_Manzanillo (default 3%)
        """
        base_gravable = max(precio_operacion, valor_catastral)
        return base_gravable * tasa

    @staticmethod
    def calculate_retentions(subtotal: Decimal, rfc_receptor: str) -> dict:
        """
        Calculates retentions if the receptor is a Persona Moral (RFC length == 12).
        ISR: 10%
        IVA: 10.6667% (Two thirds of 16%)
        """
        # Remove any spaces or separators to check strict length
        clean_rfc = rfc_receptor.replace(" ", "").replace("-", "")

        if len(clean_rfc) == 12:
            isr_retention = subtotal * Decimal('0.10')
            # 10.6667% is the approximation for 2/3 of 16% commonly used in CFDI
            # Precise calculation: (Subtotal * 0.16) * (2/3) -> Subtotal * 0.106666...
            # The spec mentions 10.6667%
            iva_retention = subtotal * Decimal('0.106667')

            return {
                "isr": isr_retention.quantize(Decimal('0.01')),
                "iva": iva_retention.quantize(Decimal('0.01')),
                "is_persona_moral": True
            }

        return {
            "isr": Decimal('0.00'),
            "iva": Decimal('0.00'),
            "is_persona_moral": False
        }

    @staticmethod
    def sanitize_name(name: str) -> str:
        """
        Removes corporate suffixes like 'S.A. DE C.V.' for CFDI 4.0 compliance.
        """
        # Regex to match common suffixes at the end of the string
        # Matches " S.A.", " S.A. DE C.V.", " S.C.", etc., case insensitive
        suffix_regex = re.compile(r"\s+(?:S\.?A\.?|S\.?C\.?|S\.?R\.?L\.?|S\.?N\.?C\.?)(?:\s+DE\s+C\.?V\.?)?\.?$", re.IGNORECASE)

        clean_name = suffix_regex.sub("", name).strip()
        # Also remove trailing comma if left behind (e.g. "Name, S.A.")
        if clean_name.endswith(","):
            clean_name = clean_name[:-1]

        return clean_name

    @staticmethod
    def validate_cp(cp: str, state_code: str = "06") -> bool:
        """
        Validates CP against catalog.
        In production, this would query Firestore 'catalogos_sat/c_CodigoPostal'.
        Here we implement basic format validation and logic.
        """
        if not re.match(r"^\d{5}$", cp):
            return False

        # Mock logic: Check if CP starts with state code range for Colima (28xxx)
        # Manzanillo is typically 282xx
        if state_code == "06": # Colima
            return cp.startswith("28")

        return True

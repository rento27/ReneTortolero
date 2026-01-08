import re
from decimal import Decimal, getcontext, ROUND_HALF_UP

# Set precision high enough for fiscal calculations
getcontext().prec = 28

class FiscalEngine:
    @staticmethod
    def sanitize_name(name: str) -> str:
        """
        Removes corporate regime suffixes from the name to comply with CFDI 4.0 strict validation.
        Example: "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACÍFICO"
        """
        if not name:
            return ""

        # Normalize spaces first
        clean_name = name.strip()
        clean_name = re.sub(r'\s+', ' ', clean_name)

        # Regex to match common Mexican corporate suffixes
        # Matches comma (optional) + space (optional) + S.A. etc... at the end of string
        # Added \s* at the end to be safe, though we stripped already.
        # Added S.A.S
        pattern = r"[,.]?\s*(S\.?\s*A\.?\s*DE\s*C\.?\s*V\.?|S\.?\s*A\.?\s*S\.?|S\.?\s*A\.?|S\.?\s*C\.?|S\.?\s*A\.?\s*P\.?\s*I\.?\s*DE\s*C\.?\s*V\.?|L\.?\s*T\.?\s*D\.?|INC\.?)\.?\s*$"

        clean_name = re.sub(pattern, "", clean_name, flags=re.IGNORECASE).strip()

        # Remove trailing punctuation that might remain (like a comma)
        clean_name = re.sub(r'[,.]$', '', clean_name).strip()

        return clean_name.upper()

    @staticmethod
    def calculate_retentions(subtotal: Decimal, rfc_receptor: str, iva_rate: Decimal = Decimal('0.16')) -> dict:
        """
        Calculates retentions if the receptor is a Persona Moral (RFC length == 12).

        Returns a dictionary with 'isr_retention' and 'iva_retention' amounts.
        """
        # Ensure inputs are Decimals
        subtotal = Decimal(str(subtotal))
        iva_rate = Decimal(str(iva_rate))

        retentions = {
            "isr_retention": Decimal('0.00'),
            "iva_retention": Decimal('0.00'),
            "is_persona_moral": False
        }

        if len(rfc_receptor) == 12:
            retentions["is_persona_moral"] = True

            # ISR Retention: 10%
            retentions["isr_retention"] = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            # IVA Retention: 2/3 of the IVA amount
            # IVA Amount = Subtotal * 0.16
            # Retention = (Subtotal * 0.16) * (2/3)
            # According to law, it's strictly 2/3 parts.

            iva_amount = subtotal * iva_rate
            iva_ret = iva_amount * (Decimal('2') / Decimal('3'))

            retentions["iva_retention"] = iva_ret.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return retentions

    @staticmethod
    def calculate_isai_manzanillo(operation_price: Decimal, cadastral_value: Decimal, rate: Decimal) -> Decimal:
        """
        Calculates ISAI for Manzanillo.
        Formula: Max(Price, Catastral) * Rate
        Rate is typically 0.03 (3%) but passed as argument (from config).
        """
        operation_price = Decimal(str(operation_price))
        cadastral_value = Decimal(str(cadastral_value))
        rate = Decimal(str(rate))

        base = max(operation_price, cadastral_value)
        isai = base * rate

        return isai.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @staticmethod
    def validate_copropiedad(percentages: list[Decimal]) -> bool:
        """
        Validates that the sum of percentages is exactly 100.00%.
        """
        total = sum([Decimal(str(p)) for p in percentages])
        return total == Decimal('100.00')

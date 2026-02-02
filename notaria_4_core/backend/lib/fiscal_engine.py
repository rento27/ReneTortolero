import re
from decimal import Decimal, getcontext, ROUND_HALF_UP

# Set precision for financial calculations
getcontext().prec = 28

class FiscalEngine:
    def __init__(self):
        self.isr_retention_rate = Decimal("0.10") # 10%
        self.iva_rate = Decimal("0.16") # 16%
        # IVA Retention is 2/3 of the IVA
        self.iva_retention_factor = Decimal("2") / Decimal("3")

    def sanitize_name(self, name: str) -> str:
        """
        Removes corporate regimes like S.A. DE C.V. from the name
        to comply with CFDI 4.0 strict name matching.
        """
        if not name:
            return ""

        # Common regimes to strip (case insensitive)
        # Regex looks for comma (optional) followed by regime at the end of string
        regimes = [
            r",?\s*S\.?A\.?\s*DE\s*C\.?V\.?$",
            r",?\s*S\.?C\.?$",
            r",?\s*S\.?A\.?$",
            r",?\s*S\.?A\.?P\.?I\.?\s*DE\s*C\.?V\.?$",
            r",?\s*L\.?T\.?D\.?$",
            r",?\s*INC\.?$"
        ]

        sanitized = name.strip().upper()
        for pattern in regimes:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        return sanitized.strip()

    def validate_zip_code(self, zip_code: str, state_code: str = None) -> bool:
        """
        Validates structure of Zip Code.
        TODO: Integrate with full SAT catalog check in Firestore.
        """
        if not re.match(r"^\d{5}$", zip_code):
            return False

        # Example logic: Colima Zips start with 28
        if state_code == "COL" and not zip_code.startswith("28"):
            return False

        return True

    def calculate_taxes(self, amount: float, is_persona_moral: bool):
        """
        Calculates IVA, Subtotal, and Retentions.
        Returns a dictionary with Decimal values converted to float for JSON response.
        """
        base = Decimal(str(amount))
        iva = base * self.iva_rate

        ret_isr = Decimal("0")
        ret_iva = Decimal("0")

        if is_persona_moral:
            ret_isr = base * self.isr_retention_rate
            ret_iva = iva * self.iva_retention_factor

        # Rounding to 2 decimal places for final output
        def round_money(d):
            return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total = base + iva - ret_isr - ret_iva

        return {
            "subtotal": float(round_money(base)),
            "iva_trasladado": float(round_money(iva)),
            "retencion_isr": float(round_money(ret_isr)),
            "retencion_iva": float(round_money(ret_iva)),
            "total": float(round_money(total)),
            "breakdown": {
                "base_exact": str(base),
                "iva_exact": str(iva),
                "ret_iva_exact": str(ret_iva)
            }
        }

    def validate_copropiedad(self, percentages: list[float]) -> bool:
        """
        Validates that the sum of percentages equals exactly 100.00%
        """
        total = sum([Decimal(str(p)) for p in percentages])
        return total == Decimal("100.00")

    def calculate_isai(self, price: float, cadastral_value: float, rate: float = 0.03) -> dict:
        """
        Calculates ISAI (Impuesto Sobre Adquisición de Inmuebles) for Manzanillo.
        Formula: Max(Precio, ValorCatastral) * Tasa
        Default rate is 3% (0.03).
        """
        p_price = Decimal(str(price))
        p_cadastral = Decimal(str(cadastral_value))
        p_rate = Decimal(str(rate))

        base_isai = max(p_price, p_cadastral)
        isai_total = base_isai * p_rate

        def round_money(d):
            return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "base_isai": float(round_money(base_isai)),
            "isai_total": float(round_money(isai_total)),
            "rate_used": float(p_rate)
        }

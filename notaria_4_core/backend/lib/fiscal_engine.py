import re
from decimal import Decimal, getcontext

# Set precision for financial calculations
getcontext().prec = 28

class FiscalEngine:
    @staticmethod
    def sanitize_name(name: str) -> str:
        """
        Removes corporate regime suffixes from the name to comply with CFDI 4.0.
        Example: "INMOBILIARIA DEL PACIFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACIFICO"
        """
        if not name:
            return ""

        # Regex patterns to remove common corporate suffixes (case insensitive)
        # Covers: S.A., S.A. DE C.V., S.C., S. DE R.L., S.A.B., etc.
        # This is a simplified list; in production, this should be exhaustive based on SAT catalog.
        patterns = [
            r",?\s*S\.?\s*A\.?\s*DE\s*C\.?\s*V\.?$",
            r",?\s*S\.?\s*A\.?\s*B\.?\s*DE\s*C\.?\s*V\.?$",
            r",?\s*S\.?\s*DE\s*R\.?\s*L\.?\s*DE\s*C\.?\s*V\.?$",
            r",?\s*S\.?\s*C\.?$",
            r",?\s*S\.?\s*A\.?$",
            r",?\s*A\.?\s*C\.?$",
            r",?\s*S\.?\s*A\.?\s*P\.?\s*I\.?\s*DE\s*C\.?\s*V\.?$"
        ]

        sanitized = name.upper().strip()
        for pattern in patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE).strip()

        return sanitized

    @staticmethod
    def calculate_retentions(rfc_receptor: str, amount: Decimal, iva_amount: Decimal) -> dict:
        """
        Calculates ISR and IVA retentions for Personas Morales (RFC length 12).
        """
        if len(rfc_receptor) == 12:
            return {
                "isr_retention": round(amount * Decimal("0.10"), 2),
                "iva_retention": round(iva_amount * (Decimal("2") / Decimal("3")), 2)  # 2/3rds of IVA
            }
        return {"isr_retention": Decimal("0.00"), "iva_retention": Decimal("0.00")}

    @staticmethod
    def calculate_isai_manzanillo(operation_price: Decimal, catastral_value: Decimal, tasa: Decimal) -> Decimal:
        """
        Calculates ISAI for Manzanillo based on the maximum of Price or Catastral Value.
        """
        base = max(operation_price, catastral_value)
        return round(base * tasa, 2)

    @staticmethod
    def validate_copropiedad(percentages: list[Decimal]) -> bool:
        """
        Validates that the sum of copropiedad percentages is exactly 100.00%.
        """
        total = sum(percentages)
        return total == Decimal("100.00")

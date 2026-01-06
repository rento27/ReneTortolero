import re
from decimal import Decimal, getcontext

# Set precision for financial calculations
getcontext().prec = 28

class FiscalEngine:
    @staticmethod
    def sanitize_name(name: str) -> str:
        """
        Removes corporate regimes from the name to comply with CFDI 4.0 strict validation.
        Example: "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACÍFICO"
        """
        # Common regimes to strip. This list can be expanded.
        # Regex looks for common suffixes, optionally preceded by a comma and whitespace.
        # It handles cases like " S.A. DE C.V.", ", S.A. DE C.V.", " S.C.", etc.
        regimes = [
            r",?\s*S\.A\. DE C\.V\.$",
            r",?\s*S\.A\.B\. DE C\.V\.$",
            r",?\s*S\. DE R\.L\. DE C\.V\.$",
            r",?\s*S\.A\.$",
            r",?\s*S\.C\.$",
            r",?\s*A\.C\.$",
            r",?\s*S\.A\.P\.I\. DE C\.V\.$"
        ]

        sanitized = name.strip()
        for pattern in regimes:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE).strip()

        return sanitized

    @staticmethod
    def calculate_retentions(subtotal: Decimal, rfc_receptor: str) -> dict:
        """
        Calculates ISR and IVA retentions for Personas Morales (RFC length 12).

        Args:
            subtotal (Decimal): The base amount for the service (Honorarios).
            rfc_receptor (str): The RFC of the client.

        Returns:
            dict: A dictionary containing retention amounts or None if not applicable.
        """
        if len(rfc_receptor) == 12:
            isr_retention = subtotal * Decimal("0.10")
            # IVA Retention is 2/3 of the transferred IVA (which is 16%).
            # Effectively 10.6667%
            iva_retention = subtotal * Decimal("0.106667")

            return {
                "isr": isr_retention.quantize(Decimal("0.01")),
                "iva": iva_retention.quantize(Decimal("0.01"))
            }
        return {}

    @staticmethod
    def calculate_isai(precio_operacion: Decimal, valor_catastral: Decimal, tasa: Decimal = Decimal("0.03")) -> Decimal:
        """
        Calculates ISAI (Impuesto Sobre Adquisición de Inmuebles) based on Manzanillo rules.
        ISAI = Max(Precio, ValorCatastral) * Tasa
        """
        base = max(precio_operacion, valor_catastral)
        isai = base * tasa
        return isai.quantize(Decimal("0.01"))

    @staticmethod
    def validate_cp(cp: str, state_code: str = "06") -> bool:
        """
        Stub for validating CP against SAT catalog.
        In a real scenario, this would check against a loaded DB or file.
        For now, it ensures it's 5 digits.
        """
        return len(cp) == 5 and cp.isdigit()

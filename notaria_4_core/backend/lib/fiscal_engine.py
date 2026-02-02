import re
from decimal import Decimal, getcontext

# Set precision for financial calculations
# Increased to 28 to handle large values (millions) accurately without overflow
getcontext().prec = 28

class FiscalEngine:
    def __init__(self):
        # Default ISAI rate for Manzanillo (can be overridden by config)
        self.isai_rate = Decimal("0.03")

    def sanitize_name(self, name: str) -> str:
        """
        Removes corporate suffixes (S.A. DE C.V., etc.) for CFDI 4.0 compliance.
        """
        cleaned_name = name.upper().strip()

        # List of common suffixes to remove.
        suffixes = [
            r"\bS\.?A\.? DE C\.?V\.?\b",
            r"\bS\.?A\.?\b",
            r"\bS\.?C\.?\b",
            r"\bS\.? DE R\.?L\.?\b",
            r"\bS\.?A\.?S\.?\b",
            r"\bA\.?C\.?\b"
        ]

        for suffix in suffixes:
            cleaned_name = re.sub(suffix, "", cleaned_name, flags=re.IGNORECASE)

        # Remove trailing punctuation (commas, periods) and whitespace
        # Repeatedly strip until clean
        cleaned_name = re.sub(r"[\.,\s]+$", "", cleaned_name).strip()

        return cleaned_name

    def validate_cp(self, cp: str, sat_catalog_provider) -> bool:
        """
        Validates the postal code against the SAT catalog (provided via dependency injection).
        """
        # Implementation would look up the CP in the injected provider
        return sat_catalog_provider.exists(cp)

    def calculate_isai(self, price: float, cadastral_value: float) -> dict:
        """
        Calculates ISAI based on Manzanillo rules: Max(Price, Cadastral) * Rate.
        """
        # Ensure inputs are treated as strings for Decimal conversion to avoid float precision issues
        base = max(Decimal(str(price)), Decimal(str(cadastral_value)))
        isai_tax = base * self.isai_rate
        return {
            "base": float(base),
            "rate": float(self.isai_rate),
            "tax": float(isai_tax.quantize(Decimal("0.01")))
        }

    def calculate_retentions(self, rfc_receiver: str, subtotal: float, iva_trasladado: float) -> dict:
        """
        Calculates retentions if the receiver is a Persona Moral (RFC length 12).
        """
        if len(rfc_receiver) == 12:
            subtotal_dec = Decimal(str(subtotal))
            iva_dec = Decimal(str(iva_trasladado))

            # ISR Retention: 10% of Subtotal
            isr_ret = subtotal_dec * Decimal("0.10")

            # IVA Retention: 2/3 of IVA Trasladado (equivalent to 10.6667% of subtotal if IVA is 16%)
            # But the law says "dos terceras partes del impuesto trasladado"
            iva_ret = (iva_dec * Decimal("2")) / Decimal("3")

            return {
                "isr_retention": float(isr_ret.quantize(Decimal("0.01"))),
                "iva_retention": float(iva_ret.quantize(Decimal("0.01"))),
                "is_persona_moral": True
            }
        return {
            "isr_retention": 0.0,
            "iva_retention": 0.0,
            "is_persona_moral": False
        }

    def calculate_total(self, data: dict) -> dict:
        """
        Orchestrates the full calculation.
        Expected data keys: 'rfc_receiver', 'subtotal', 'iva_trasladado' (optional),
        'price' (optional), 'cadastral_value' (optional)
        """
        subtotal = data.get('subtotal', 0.0)
        # Assuming standard IVA 16% if not provided
        iva_trasladado = data.get('iva_trasladado', subtotal * 0.16)

        rfc = data.get('rfc_receiver', '')

        retentions = self.calculate_retentions(rfc, subtotal, iva_trasladado)

        isai = {}
        if 'price' in data and 'cadastral_value' in data:
            isai = self.calculate_isai(data['price'], data['cadastral_value'])

        total = Decimal(str(subtotal)) + Decimal(str(iva_trasladado)) - Decimal(str(retentions['isr_retention'])) - Decimal(str(retentions['iva_retention']))

        return {
            "subtotal": subtotal,
            "iva_trasladado": iva_trasladado,
            "retentions": retentions,
            "isai": isai,
            "total": float(total.quantize(Decimal("0.01")))
        }

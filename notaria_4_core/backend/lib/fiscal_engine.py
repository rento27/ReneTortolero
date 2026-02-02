import re
import unicodedata
from decimal import Decimal, getcontext

# Set Decimal precision high enough for fiscal calculations
getcontext().prec = 10

class FiscalEngine:
    @staticmethod
    def sanitize_name(name: str) -> str:
        """
        Removes corporate regimes from company names to match SAT CFDI 4.0 requirements.
        Example: "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACIFICO"
        Also removes accents/diacritics.
        """
        if not name:
            return ""

        # Normalize accents (Á -> A, etc.)
        nfkd_form = unicodedata.normalize('NFKD', name)
        ascii_name = "".join([c for c in nfkd_form if not unicodedata.combining(c)])

        sanitized = ascii_name.strip().upper()

        # Regex to remove common corporate suffixes (S.A. DE C.V., S. DE R.L., etc.)
        # We check for the suffix at the end of the string.
        # Note: Order matters (longest matches first usually safer, but here we just iterate)
        regimes = [
            r",? S\.?A\.? DE C\.?V\.?",
            r",? S\.?A\.?P\.?I\.? DE C\.?V\.?",
            r",? S\.? DE R\.?L\.? DE C\.?V\.?",
            r",? S\.?A\.?B\.? DE C\.?V\.?",
            r",? S\.?A\.?",
            r",? S\.?C\.?",
            r",? A\.?C\.?",
            r",? S\.?A\.?S\.?",
            r",? S\.? EN C\.?",
            r",? S\.? EN C\.? POR A\.?",
            r",? S\.? DE R\.?L\.?"
        ]

        for regime in regimes:
            sanitized = re.sub(regime + "$", "", sanitized, flags=re.IGNORECASE).strip()

        return sanitized

    @staticmethod
    def calculate_isai(precio_operacion: Decimal, valor_catastral: Decimal, tasa: Decimal = Decimal('0.03')) -> Decimal:
        """
        Calculates ISAI for Manzanillo.
        Formula: Max(Precio, Catastral) * Tasa
        """
        base = max(precio_operacion, valor_catastral)
        return base * tasa

    @staticmethod
    def get_retentions_persona_moral(rfc: str, subtotal: Decimal) -> dict:
        """
        Determines retentions if the receptor is a Persona Moral (RFC len 12).
        Returns dictionary with retention amounts.
        """
        if len(rfc) == 12:
            # Persona Moral rules
            isr_ret = subtotal * Decimal('0.10')

            # IVA Retention: 2/3 of 16%
            # IVA Rate is 0.16
            iva_rate = Decimal('0.16')
            iva_traslado = subtotal * iva_rate
            iva_ret = iva_traslado * Decimal('2') / Decimal('3')

            return {
                "retencion_isr": isr_ret,
                "retencion_iva": iva_ret,
                "is_persona_moral": True
            }
        return {
            "retencion_isr": Decimal('0.00'),
            "retencion_iva": Decimal('0.00'),
            "is_persona_moral": False
        }

    @staticmethod
    def validate_copropiedad(percentages: list[Decimal]) -> bool:
        """
        Validates that the sum of copropiedad percentages is exactly 100.00%
        """
        total = sum(percentages)
        # Compare with tolerance or exact? Blueprint says "Exactamente".
        # Using Decimal comparison.
        return total == Decimal('100.00')

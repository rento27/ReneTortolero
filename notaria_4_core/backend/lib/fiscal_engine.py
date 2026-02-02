import re
from decimal import Decimal, ROUND_HALF_UP

class FiscalEngine:
    def __init__(self):
        # Manzanillo ISAI rate
        # TODO: Load this from Firebase Remote Config instead of hardcoding
        self.TASA_ISAI_MANZANILLO = Decimal("0.03")

        # Regex to strip corporate regimes
        self.REGIME_REGEX = re.compile(
            r",?\s+(S\.?A\.?\s+DE\s+C\.?V\.?|S\.?C\.?|S\.?A\.?P\.?I\.?\s+DE\s+C\.?V\.?|S\.?A\.?|A\.?C\.?|S\.? DE R\.?L\.?|S\.?A\.?S\.?)\s*$",
            re.IGNORECASE
        )

    def sanitize_name(self, raw_name: str) -> str:
        """
        Removes corporate regime from the name as per CFDI 4.0 strict rules.
        Example: 'INMOBILIARIA DEL PACÍFICO, S.A. DE C.V.' -> 'INMOBILIARIA DEL PACÍFICO'
        """
        if not raw_name:
            return ""

        clean_name = raw_name.strip().upper()
        clean_name = self.REGIME_REGEX.sub("", clean_name)
        return clean_name.strip()

    def validate_zip_code(self, zip_code: str, state_code: str) -> bool:
        """
        Validates zip code against state.
        This is a simplified check.
        TODO: Implement strict lookup against c_CodigoPostal in Firestore/Storage.
        Colima Zips usually start with '28'.
        """
        if state_code == '06' or state_code == 'COL': # Colima
            return zip_code.startswith('28')
        return True # Default pass for other states for now

    def calculate_isai(self, price: Decimal, catastral: Decimal) -> Decimal:
        """
        Calculates ISAI for Manzanillo.
        Formula: Max(Price, Catastral) * Rate
        """
        base = max(price, catastral)
        return (base * self.TASA_ISAI_MANZANILLO).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_retentions(self, subtotal: Decimal, rfc_receptor: str) -> dict:
        """
        Calculates retentions if the receptor is a Persona Moral (RFC len 12).
        Returns dictionary with retention amounts.
        """
        retentions = {
            "isr_ret": Decimal("0.00"),
            "iva_ret": Decimal("0.00"),
            "is_persona_moral": False
        }

        # Check for Persona Moral (RFC length 12)
        if len(rfc_receptor) == 12:
            retentions["is_persona_moral"] = True

            # ISR Retention: 10%
            retentions["isr_ret"] = (subtotal * Decimal("0.10")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # IVA Retention: 2/3 of IVA (16%)
            # IVA Rate = 0.16
            # Retention Rate = 0.16 * (2/3) = 0.106666...

            full_iva = subtotal * Decimal("0.16")
            iva_ret = full_iva * (Decimal("2") / Decimal("3"))

            retentions["iva_ret"] = iva_ret.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return retentions

    def validate_copropiedad(self, percentages: list[Decimal]) -> bool:
        """
        Validates that the sum of copropiedad percentages is exactly 100.00%.
        """
        total = sum(percentages)
        # Strictly we expect Decimals.
        return total == Decimal("100.00")

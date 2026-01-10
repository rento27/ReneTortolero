import re
from decimal import Decimal, getcontext, ROUND_HALF_UP

# Set precision for financial calculations
getcontext().prec = 28

class FiscalEngine:
    @staticmethod
    def sanitize_name(name: str) -> str:
        """
        Removes corporate regimes from the name to comply with CFDI 4.0 strict validation.
        Example: "INMOBILIARIA DEL PACÍFICO, S.A. DE C.V." -> "INMOBILIARIA DEL PACÍFICO"
        """
        # List of common regimes to strip (this list should be comprehensive in production)
        regimes = [
            r",? S\.A\. DE C\.V\.", r",? S\.A\.", r",? S\.C\.", r",? S\. DE R\.L\.",
            r",? S\.A\.P\.I\.", r",? S\.A\.S\.", r",? A\.C\."
        ]

        sanitized = name.upper().strip()
        for regime in regimes:
            sanitized = re.sub(regime, "", sanitized, flags=re.IGNORECASE)

        return sanitized.strip()

    @staticmethod
    def calculate_isai_manzanillo(operation_price: Decimal, cadastral_value: Decimal, rate: Decimal = Decimal('0.03')) -> Decimal:
        """
        Calculates ISAI for Manzanillo.
        Formula: Max(Price, Cadastral) * Rate.
        """
        base = max(operation_price, cadastral_value)
        return (base * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def calculate_retentions_persona_moral(subtotal: Decimal, iva_rate: Decimal = Decimal('0.16')) -> dict:
        """
        Calculates retentions if the receiver is a Persona Moral.
        Returns dictionary with ISR and IVA retention amounts.
        """
        # ISR Retention: 10%
        isr_retention = (subtotal * Decimal('0.10')).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # IVA Retention: 2/3 of IVA
        # IVA full amount
        iva_amount = subtotal * iva_rate
        # 2/3 calculation: (IVA * 2) / 3 OR 10.6667% direct approx depending on legal interpretation.
        # The prompt specifies: "Matemáticamente, esto equivale a una tasa del 10.6667%"
        # But rigorous approach is usually (IVA / 3) * 2

        # Using the prompt's implied rate for consistency if strict:
        # However, satcfdi usually handles tax rates. If we manually calculate:
        iva_retention = (subtotal * Decimal('0.106667')).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "isr_retention": isr_retention,
            "iva_retention": iva_retention
        }

    @staticmethod
    def validate_copropiedad(percentages: list[Decimal]) -> bool:
        """
        Validates that the sum of copropiedad percentages is exactly 100.00%.
        """
        total = sum(percentages)
        return total == Decimal('100.00')

    @staticmethod
    def validate_zip_code(zip_code: str, state_code: str) -> bool:
        """
        Validates the zip code against the local copy of SAT's c_CodigoPostal catalog.
        In production, this would query Firestore or a loaded JSON.
        """
        # TODO: Load catalog from Firestore/JSON
        # For prototype, we validate length and format
        if not re.match(r"^\d{5}$", zip_code):
            return False

        # Mock validation: Colima zips start with 28
        if state_code == "COL" and not zip_code.startswith("28"):
             return False

        return True

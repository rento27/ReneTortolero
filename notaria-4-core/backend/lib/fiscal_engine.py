from decimal import Decimal, ROUND_HALF_UP

class FiscalEngine:
    def __init__(self):
        # Default Manzanillo ISAI rate (can be overridden by Remote Config in future)
        self.ISAI_RATE_MANZANILLO = Decimal('0.03')

    def is_persona_moral(self, rfc: str) -> bool:
        """
        Determines if an RFC belongs to a Persona Moral based on length.
        RFC Persona Moral: 12 chars
        RFC Persona Fisica: 13 chars
        """
        return len(rfc.strip()) == 12

    def calculate_taxes(self, subtotal: float, is_persona_moral: bool) -> dict:
        """
        Calculates IVA and Retentions based on the entity type.
        """
        subtotal_dec = Decimal(str(subtotal))
        iva_rate = Decimal('0.16')

        iva_trasladado = subtotal_dec * iva_rate

        retentions = {
            'isr': Decimal('0.00'),
            'iva': Decimal('0.00')
        }

        if is_persona_moral:
            # Retention Logic:
            # ISR: 10%
            retentions['isr'] = subtotal_dec * Decimal('0.10')

            # IVA Retention: 2/3 of IVA Trasladado (approx 10.6667%)
            # Precision is critical here.
            retentions['iva'] = (iva_trasladado * Decimal('2') / Decimal('3'))

        return {
            'subtotal': float(subtotal_dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'iva_trasladado': float(iva_trasladado.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'ret_isr': float(retentions['isr'].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'ret_iva': float(retentions['iva'].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            'total_retentions': float((retentions['isr'] + retentions['iva']).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        }

    def calculate_isai_manzanillo(self, precio_operacion: float, valor_catastral: float) -> float:
        """
        ISAI = Max(Precio, ValorCatastral) * Tasa_Manzanillo
        """
        base = max(precio_operacion, valor_catastral)
        isai = Decimal(str(base)) * self.ISAI_RATE_MANZANILLO
        return float(isai.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

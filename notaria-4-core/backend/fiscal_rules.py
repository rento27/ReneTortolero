from decimal import Decimal, ROUND_HALF_UP

def calculate_retentions(rfc: str, subtotal: float):
    """
    Calculates retentions for Personas Morales (RFC length 12).
    Returns a dictionary with retention amounts or None if Persona Fisica.
    """
    rfc = rfc.strip().upper()

    # Check if Persona Moral (12 characters)
    if len(rfc) == 12:
        # Use Decimal for high precision math
        base = Decimal(str(subtotal))

        # ISR: 10%
        isr_rate = Decimal("0.10")
        isr_amount = (base * isr_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # IVA Retention: Two-thirds of IVA (16%)
        # Effectively 10.6667%
        # Math: (IVA_Trasladado * 2) / 3
        # IVA Trasladado = Base * 0.16
        iva_trasladado = base * Decimal("0.16")
        iva_ret_amount = (iva_trasladado * Decimal("2") / Decimal("3")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "type": "Persona Moral",
            "retentions": {
                "ISR_001": float(isr_amount),
                "IVA_002": float(iva_ret_amount)
            },
            "total_retention": float(isr_amount + iva_ret_amount)
        }

    return {
        "type": "Persona Fisica",
        "retentions": None,
        "total_retention": 0.0
    }

def calculate_isai(precio_operacion: float, valor_catastral: float, tasa: float):
    """
    Calculates ISAI for Manzanillo based on the maximum value between operation price and cadastral value.
    """
    base_gravable = max(precio_operacion, valor_catastral)
    impuesto = base_gravable * tasa
    return {
        "base_gravable": base_gravable,
        "tasa_aplicada": tasa,
        "isai_total": round(impuesto, 2)
    }

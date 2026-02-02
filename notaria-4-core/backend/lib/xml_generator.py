from satcfdi.create.cfd import cfdi40
from satcfdi.create.cfd.catalogos import RegimenFiscal, UsoCFDI, MetodoPago, FormaPago, TipoDeComprobante, TipoFactor, Impuesto
from decimal import Decimal

# MOCK Classes for Notarios Publicos Complement
# In a real scenario, we would generate these from the XSD using `satcfdi`'s tools
# or import them if available. For now, we structure them as generic dicts/objects
# compatible with satcfdi's flexibility.

class XMLGenerator:
    def __init__(self, signer=None):
        self.signer = signer

    def generate_cfdi(self, data: dict, tax_calculations: dict) -> cfdi40.Comprobante:
        """
        Builds the CFDI 4.0 Object.
        """

        # 1. Impuestos Logic

        traslados_list = [
            cfdi40.Traslado(
                base=Decimal(str(tax_calculations['subtotal'])),
                impuesto=Impuesto.IVA,
                tipo_factor=TipoFactor.TASA,
                tasa_o_cuota=Decimal('0.160000'),
                # Importe auto-calculated by satcfdi
            )
        ]

        retenciones_list = []
        if tax_calculations['ret_isr'] > 0:
            retenciones_list.append(
                cfdi40.Retencion(
                    base=Decimal(str(tax_calculations['subtotal'])),
                    impuesto=Impuesto.ISR,
                    tipo_factor=TipoFactor.TASA,
                    tasa_o_cuota=Decimal('0.100000')
                )
            )

        if tax_calculations['ret_iva'] > 0:
            retenciones_list.append(
                cfdi40.Retencion(
                    base=Decimal(str(tax_calculations['subtotal'])),
                    impuesto=Impuesto.IVA,
                    tipo_factor=TipoFactor.TASA,
                    tasa_o_cuota=Decimal('0.106667')
                )
            )

        impuestos_concepto = cfdi40.Impuestos(
            traslados=traslados_list,
            retenciones=retenciones_list if retenciones_list else None
        )

        # Remove 'importe' from kwargs. satcfdi calculates it based on cantidad * valor_unitario
        concepto = cfdi40.Concepto(
            clave_prod_serv='80121603', # Servicios legales de derecho notarial
            no_identificacion='HONORARIOS',
            cantidad=Decimal('1'),
            clave_unidad='E48',
            unidad='SERVICIO',
            descripcion='HONORARIOS NOTARIALES ESCRITURA ' + str(data.get('escritura', '')),
            valor_unitario=Decimal(str(tax_calculations['subtotal'])),
            objeto_imp='02',
            impuestos=impuestos_concepto
        )

        # 3. Build Comprobante using lowercase arguments per documentation
        # NOTE: sub_total and total are calculated automatically by satcfdi if omitted,
        # derived from the sum of conceptos.
        cfdi = cfdi40.Comprobante(
            emisor=cfdi40.Emisor(
                rfc='TOSR520601AZ4',
                nombre='RENE MANUEL TORTOLERO SANTILLANA',
                regimen_fiscal='612' # Personas Físicas con Actividades Empresariales
            ),
            receptor=cfdi40.Receptor(
                rfc=data['rfc'],
                nombre=data['razon_social'], # Sanitized name
                uso_cfdi=data.get('uso_cfdi', 'G03'),
                domicilio_fiscal_receptor=data.get('cp_receptor', '28219'), # Example
                regimen_fiscal_receptor='601' # General de Ley Personas Morales (Example)
            ),
            lugar_expedicion='28869',
            metodo_pago=MetodoPago.PAGO_EN_UNA_SOLA_EXHIBICION,
            forma_pago='03', # Transferencia
            moneda='MXN',
            tipo_de_comprobante=TipoDeComprobante.INGRESO,
            exportacion='01', # No aplica
            conceptos=[concepto],
            # complemento=complement # Add later
        )

        # Sign if signer is available
        if self.signer:
            cfdi.sign(self.signer)

        return cfdi

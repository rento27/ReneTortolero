from decimal import Decimal
from datetime import datetime
from satcfdi.create.cfd import cfdi40
from satcfdi.create.cfd.notariospublicos10 import (
    NotariosPublicos, DescInmueble, DatosOperacion, DatosNotario,
    DatosEnajenante, DatosUnEnajenante, DatosAdquiriente, DatosUnAdquiriente
)
from satcfdi.create.cfd.catalogos import RegimenFiscal, UsoCFDI, MetodoPago, TipoDeComprobante, Exportacion
from .fiscal_engine import sanitize_name, get_retention_rates

class XMLGenerator:
    def __init__(self, signer):
        """
        Initializes the generator with a Signer (CSD loaded).
        """
        self.signer = signer

    def generate_invoice(self, invoice_data: dict, notary_data: dict):
        """
        Generates a signed CFDI 4.0 with Notarios Publicos complement.

        Args:
            invoice_data: Dict containing 'receptor', 'conceptos', 'forma_pago', etc.
            notary_data: Dict containing 'num_notaria', 'datos_operacion', 'inmueble', etc.
        """

        # 1. Sanitize Receptor Name
        receptor_name = sanitize_name(invoice_data['receptor']['razon_social'])
        receptor_rfc = invoice_data['receptor']['rfc']

        # 2. Calculate Retentions (Persona Moral)
        retention_rates = get_retention_rates(receptor_rfc)

        # 3. Process Concepts
        conceptos = []
        subtotal = Decimal('0.00')
        total_impuestos_trasladados = Decimal('0.00')
        total_impuestos_retenidos = Decimal('0.00')

        for item in invoice_data['conceptos']:
            importe = Decimal(str(item['importe']))
            valor_unitario = Decimal(str(item['valor_unitario']))
            cantidad = Decimal(str(item['cantidad']))

            # Basic validation
            if importe != (valor_unitario * cantidad):
                 # For simplicity, we trust importe or recalc it. Let's recalc.
                 importe = valor_unitario * cantidad

            subtotal += importe

            concepto = {
                'clave_prod_serv': item['clave_prod_serv'],
                'cantidad': cantidad,
                'clave_unidad': item['clave_unidad'],
                'descripcion': item['descripcion'],
                'valor_unitario': valor_unitario,
                'objeto_imp': item['objeto_imp']
            }

            # Tax Logic (Only if ObjetoImp == '02')
            if item['objeto_imp'] == '02':
                # Traslados (IVA 16%)
                base = importe
                iva_tras = base * Decimal('0.16')

                traslados = [cfdi40.Traslado(
                    base=base,
                    impuesto='002', # IVA
                    tipo_factor='Tasa',
                    tasa_o_cuota=Decimal('0.160000'),
                    importe=iva_tras
                )]

                total_impuestos_trasladados += iva_tras

                # Retentions (if applicable)
                retenciones = []
                if retention_rates['isr_rate'] > 0:
                    isr_ret = base * retention_rates['isr_rate']
                    retenciones.append(cfdi40.Retencion(
                        base=base,
                        impuesto='001', # ISR
                        tipo_factor='Tasa',
                        tasa_o_cuota=retention_rates['isr_rate'],
                        importe=isr_ret
                    ))
                    total_impuestos_retenidos += isr_ret

                if retention_rates['iva_rate'] > 0:
                    iva_ret = base * retention_rates['iva_rate']
                    retenciones.append(cfdi40.Retencion(
                        base=base,
                        impuesto='002', # IVA
                        tipo_factor='Tasa',
                        tasa_o_cuota=retention_rates['iva_rate'], # 0.106667
                        importe=iva_ret
                    ))
                    total_impuestos_retenidos += iva_ret

                concepto['impuestos'] = cfdi40.Impuestos(
                    traslados=traslados,
                    retenciones=retenciones if retenciones else None
                )

            # Convert to explicit Concepto object to ensure types are preserved
            conceptos.append(cfdi40.Concepto(**concepto))

        # 4. Global Taxes Node
        impuestos_globales = {}
        if total_impuestos_trasladados > 0:
            impuestos_globales['Traslados'] = [{
                'Base': subtotal, # Simplified: assuming all items have same tax
                'Impuesto': '002',
                'TipoFactor': 'Tasa',
                'TasaOCuota': Decimal('0.160000'),
                'Importe': total_impuestos_trasladados
            }]

        if total_impuestos_retenidos > 0:
            impuestos_globales['Retenciones'] = []
            if retention_rates['isr_rate'] > 0:
                impuestos_globales['Retenciones'].append({
                    'Impuesto': '001',
                    'Importe': subtotal * retention_rates['isr_rate']
                })
            if retention_rates['iva_rate'] > 0:
                 impuestos_globales['Retenciones'].append({
                    'Impuesto': '002',
                    'Importe': subtotal * retention_rates['iva_rate']
                })

        total = subtotal + total_impuestos_trasladados - total_impuestos_retenidos

        # 5. Build Complemento Notarios
        complemento_notarios = self._build_complemento_notarios(notary_data)

        # 6. Create CFDI Object
        # Note: satcfdi v4 automatically calculates SubTotal, Total, and Global Taxes from Conceptos.
        cfdi = cfdi40.Comprobante(
            emisor={
                'Rfc': self.signer.rfc,
                'Nombre': 'RENÉ MANUEL TORTOLERO SANTILLANA',
                'RegimenFiscal': '612' # Personas Físicas con Actividades Empresariales y Profesionales
            },
            receptor={
                'Rfc': receptor_rfc,
                'Nombre': receptor_name,
                'UsoCFDI': invoice_data['receptor']['uso_cfdi'],
                'DomicilioFiscalReceptor': invoice_data['receptor']['cp'],
                'RegimenFiscalReceptor': invoice_data['receptor']['regimen_fiscal']
            },
            lugar_expedicion='28219', # Manzanillo
            metodo_pago=invoice_data.get('metodo_pago', 'PUE'),
            forma_pago=invoice_data.get('forma_pago', '03'), # Transferencia
            tipo_de_comprobante='I',
            exportacion='01',
            moneda='MXN',
            conceptos=conceptos,
            complemento=complemento_notarios
        )

        # 7. Sign
        cfdi.sign(self.signer)

        return cfdi.xml_bytes()

    def _build_complemento_notarios(self, data: dict):
        """
        Constructs the 'Complemento de Notarios Públicos' object using satcfdi.
        """
        # Note: We use snake_case keys for the dicts passed to constructors

        return NotariosPublicos(
            desc_inmuebles=[DescInmueble(
                tipo_inmueble=data['inmueble']['tipo'],
                calle=data['inmueble']['calle'],
                municipio=data['inmueble']['municipio'],
                estado=data['inmueble']['estado'],
                pais="MEX",
                codigo_postal=data['inmueble']['cp']
            )],
            datos_operacion=DatosOperacion(
                num_instrumento_notarial=data['operacion']['num_instrumento'],
                fecha_inst_notarial=datetime.strptime(data['operacion']['fecha_instrumento'], '%Y-%m-%d').date(),
                monto_operacion=Decimal(str(data['operacion']['monto'])),
                subtotal=Decimal(str(data['operacion']['subtotal'])),
                iva=Decimal(str(data['operacion']['iva']))
            ),
            datos_notario=DatosNotario(
                curp=data['notario']['curp'],
                num_notaria=int(data['notario']['numero']),
                entidad_federativa=data['notario']['entidad'],
                adscripcion=data['notario']['adscripcion']
            ),
            datos_enajenante=DatosEnajenante(
                copro_soc_conyugal_e=data.get('copro_soc_conyugal_enajenante', 'No'),
                datos_un_enajenante=DatosUnEnajenante(
                    nombre=(data.get('enajenantes', []) or [{'nombre': 'ENAJENANTE'}])[0].get('nombre', 'ENAJENANTE'),
                    apellido_paterno=(data.get('enajenantes', []) or [{'apellido_paterno': 'GENERICO'}])[0].get('apellido_paterno', 'GENERICO'),
                    rfc=(data.get('enajenantes', []) or [{'rfc': 'XAXX010101000'}])[0].get('rfc', 'XAXX010101000'),
                    curp=(data.get('enajenantes', []) or [{'curp': 'AAAA010101HCOLXX00'}])[0].get('curp', 'AAAA010101HCOLXX00')
                )
            ),
            datos_adquiriente=DatosAdquiriente(
                copro_soc_conyugal_e=data.get('copro_soc_conyugal_adquiriente', 'No'),
                datos_un_adquiriente=DatosUnAdquiriente(
                    nombre=(data.get('adquirientes', []) or [{'Nombre': 'ADQUIRIENTE'}])[0].get('Nombre'),
                    rfc=(data.get('adquirientes', []) or [{'Rfc': 'XAXX010101000'}])[0].get('Rfc')
                ) if data.get('adquirientes') else None
            )
        )

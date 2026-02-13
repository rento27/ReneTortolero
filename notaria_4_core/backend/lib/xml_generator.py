from decimal import Decimal
import logging
from satcfdi.create.cfd import cfdi40
from satcfdi.models import Signer

from .fiscal_engine import validate_copropiedad
from .api_models import ComplementoNotariosModel
from .complement_notarios import create_complemento_notarios

logger = logging.getLogger(__name__)

def generate_signed_xml(invoice_data: dict) -> bytes:
    """
    Generates a CFDI 4.0 XML object using satcfdi.
    """

    # 1. Pre-generation Validation
    if 'copropietarios' in invoice_data and invoice_data['copropietarios']:
        percentages = [Decimal(str(p['porcentaje'])) for p in invoice_data['copropietarios']]
        validate_copropiedad(percentages)

    # 2. Prepare Concepts
    # Determine if Receptor is Persona Moral (RFC length 12)
    receptor_rfc = invoice_data['receptor']['rfc']
    is_moral = len(receptor_rfc.strip()) == 12

    conceptos_objs = []
    for c in invoice_data['conceptos']:
        impuestos_dict = None

        # Calculate Taxes if object is '02'
        if c['objeto_imp'] == '02':
            # IVA Traslado 16%
            traslados = [{
                'Impuesto': '002',
                'TipoFactor': 'Tasa',
                'TasaOCuota': Decimal('0.160000'),
                'Base': Decimal(str(c['cantidad'])) * Decimal(str(c['valor_unitario']))
            }]

            retenciones = []
            if is_moral:
                # ISR Retention 10%
                retenciones.append({
                    'Impuesto': '001',
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': Decimal('0.100000'),
                    'Base': Decimal(str(c['cantidad'])) * Decimal(str(c['valor_unitario']))
                })
                # IVA Retention 10.6667%
                retenciones.append({
                    'Impuesto': '002',
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': Decimal('0.106667'),
                    'Base': Decimal(str(c['cantidad'])) * Decimal(str(c['valor_unitario']))
                })

            impuestos_dict = {'Traslados': traslados}
            if retenciones:
                impuestos_dict['Retenciones'] = retenciones

        # Create Concepto
        # Note: satcfdi calculates Importe = Cantidad * ValorUnitario

        conceptos_objs.append(cfdi40.Concepto(
            clave_prod_serv=c['clave_prod_serv'],
            cantidad=Decimal(str(c['cantidad'])),
            clave_unidad=c['clave_unidad'],
            descripcion=c['descripcion'],
            valor_unitario=Decimal(str(c['valor_unitario'])),
            objeto_imp=c['objeto_imp'],
            impuestos=impuestos_dict
        ))

    # 3. Construct Comprobante
    try:
        receptor_data = invoice_data['receptor']
        regimen_receptor = receptor_data.get('regimen_fiscal', '616')
        if not regimen_receptor:
             regimen_receptor = '616'

        # Helper for Complement
        complemento_obj = None
        if 'complemento_notarios' in invoice_data and invoice_data['complemento_notarios']:
            try:
                comp_model = ComplementoNotariosModel(**invoice_data['complemento_notarios'])
                complemento_obj = create_complemento_notarios(comp_model)
            except Exception as e:
                logger.error(f"Error generating Complemento Notarios: {e}")
                raise ValueError(f"Error creating Complemento Notarios: {str(e)}")

        cfdi = cfdi40.Comprobante(
            emisor={
                'Rfc': 'TOSR520601AZ4',
                'RegimenFiscal': '612',
                'Nombre': 'RENE MANUEL TORTOLERO SANTILLANA'
            },
            receptor={
                'Rfc': receptor_data['rfc'],
                'Nombre': receptor_data['nombre'],
                'UsoCFDI': receptor_data['uso_cfdi'],
                'DomicilioFiscalReceptor': receptor_data['domicilio_fiscal'],
                'RegimenFiscalReceptor': regimen_receptor
            },
            lugar_expedicion='28200',
            conceptos=conceptos_objs,
            moneda='MXN',
            tipo_de_comprobante='I',
            exportacion='01',
            complemento=complemento_obj
            # SubTotal, Total, Impuestos are calculated automatically
        )

        # 5. Return XML
        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e

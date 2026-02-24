from decimal import Decimal
import logging

try:
    from satcfdi.create.cfd import cfdi40
    from satcfdi.models import Signer
except ImportError:
    cfdi40 = None
    Signer = None

from .fiscal_engine import calculate_retentions, sanitize_name
from .api_models import ComplementoNotariosModel
from .complement_notarios import create_complemento_notarios

logger = logging.getLogger(__name__)

def generate_signed_xml(invoice_data: dict) -> bytes:
    """
    Generates a CFDI 4.0 XML object using satcfdi.
    Automatically handles tax calculations and Complemento Notarios.
    """

    if not cfdi40:
        logger.error("satcfdi library not found")
        return b"<error>satcfdi not available</error>"

    # 1. Determine Fiscal Status (Persona Moral Check)
    # We use the fiscal engine logic but apply it at the Concept level for satcfdi automation
    retentions = calculate_retentions(invoice_data['receptor']['rfc'], Decimal("0")) # Amount unused here, just checking type
    is_moral = retentions['is_moral']

    # 2. Build Conceptos with Taxes
    conceptos = []
    for c in invoice_data['conceptos']:
        cantidad = Decimal(str(c['cantidad']))
        valor_unitario = Decimal(str(c['valor_unitario']))
        importe = cantidad * valor_unitario # Calculated for logic, but satcfdi computes it too.

        concepto_args = {
            'ClaveProdServ': c['clave_prod_serv'],
            'Cantidad': cantidad,
            'ClaveUnidad': c['clave_unidad'],
            'Descripcion': c['descripcion'],
            'ValorUnitario': valor_unitario,
            'ObjetoImp': c['objeto_imp']
        }

        # Tax Logic
        if c['objeto_imp'] == '02':
            # Base for taxes is the Importe (Cantidad * ValorUnitario)
            # We define the tax structure. satcfdi will calculate amounts if we pass Rates.

            traslados = {
                '002': cfdi40.Impuesto(TasaOCuota="0.160000", TipoFactor="Tasa")
            }

            rets = {}
            if is_moral:
                # Add Retentions
                rets['001'] = cfdi40.Impuesto(TasaOCuota="0.100000", TipoFactor="Tasa") # ISR
                rets['002'] = cfdi40.Impuesto(TasaOCuota="0.106667", TipoFactor="Tasa") # IVA

            impuestos_args = {
                'Traslados': traslados
            }
            if rets:
                impuestos_args['Retenciones'] = rets

            concepto_args['Impuestos'] = impuestos_args

        conceptos.append(concepto_args)

    # 3. Create Complemento Notarios
    complemento = None
    if invoice_data.get('complemento_notarios'):
        try:
            # Re-instantiate model to ensure validation and type safety
            comp_model = ComplementoNotariosModel(**invoice_data['complemento_notarios'])
            complemento = create_complemento_notarios(comp_model)
        except Exception as e:
            logger.error(f"Error creating Complemento Notarios: {e}")
            raise ValueError(f"Invalid Complemento Notarios data: {e}")

    # 4. Construct Comprobante
    try:
        # satcfdi v4 auto-calculates SubTotal, Total, and Root Impuestos from Conceptos
        cfdi = cfdi40.Comprobante(
            Emisor={
                'Rfc': 'TOSR520601AZ4',
                'RegimenFiscal': '612',
                'Nombre': 'RENE MANUEL TORTOLERO SANTILLANA'
            },
            Receptor={
                'Rfc': invoice_data['receptor']['rfc'],
                'Nombre': sanitize_name(invoice_data['receptor']['nombre']),
                'UsoCFDI': invoice_data['receptor']['uso_cfdi'],
                'DomicilioFiscalReceptor': invoice_data['receptor']['domicilio_fiscal'],
                'RegimenFiscalReceptor': invoice_data['receptor']['regimen_fiscal']
            },
            Conceptos=conceptos,
            Moneda='MXN',
            TipoDeComprobante='I',
            LugarExpedicion='28200',
            Exportacion='01',
            Complemento=complemento
        )

        # 5. Signing (Mock)
        # return cfdi.sign(signer).xml_bytes()
        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e

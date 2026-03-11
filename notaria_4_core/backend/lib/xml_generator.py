from decimal import Decimal
import logging

try:
    from satcfdi.create.cfd import cfdi40
except ImportError:
    cfdi40 = None

from .fiscal_engine import validate_copropiedad, calculate_retentions, sanitize_name
from .security import load_signer_from_secret_manager

logger = logging.getLogger(__name__)


def generate_signed_xml(invoice_data: dict) -> bytes:
    """
    Generates a CFDI 4.0 XML object using satcfdi v4 structure.
    """
    if not cfdi40:
        logger.error("satcfdi library not found")
        return b"<error>satcfdi not available</error>"

    if 'copropietarios' in invoice_data and invoice_data['copropietarios']:
        percentages = [Decimal(str(p['porcentaje'])) for p in invoice_data['copropietarios']]
        validate_copropiedad(percentages)

    try:
        # Construct Conceptos, removing Importe as it's calculated automatically
        conceptos = []
        for c in invoice_data['conceptos']:
            concepto_dict = {
                'ClaveProdServ': c['clave_prod_serv'],
                'Cantidad': Decimal(str(c['cantidad'])),
                'ClaveUnidad': c['clave_unidad'],
                'Descripcion': c['descripcion'],
                'ValorUnitario': Decimal(str(c['valor_unitario'])),
                'ObjetoImp': c['objeto_imp']
            }

            # Tax Logic for Conceptos
            # In satcfdi v4, Impuestos must be attached to the concept if we want them aggregated
            if c['objeto_imp'] == '02':
                impuestos_concepto = {}

                # IVA Trasladado (16%)
                impuestos_concepto['Traslados'] = [
                    {
                        'Base': Decimal(str(c['cantidad'])) * Decimal(str(c['valor_unitario'])),
                        'Impuesto': '002',
                        'TipoFactor': 'Tasa',
                        'TasaOCuota': Decimal('0.160000'),
                        # Importe is omitted as it is calculated
                    }
                ]

                # Check for retentions
                retentions = calculate_retentions(invoice_data['receptor']['rfc'], Decimal(str(c['cantidad'])) * Decimal(str(c['valor_unitario'])))
                if retentions['is_moral']:
                    impuestos_concepto['Retenciones'] = [
                        {
                            'Base': Decimal(str(c['cantidad'])) * Decimal(str(c['valor_unitario'])),
                            'Impuesto': '001',
                            'TipoFactor': 'Tasa',
                            'TasaOCuota': Decimal('0.100000')
                        },
                        {
                            'Base': Decimal(str(c['cantidad'])) * Decimal(str(c['valor_unitario'])),
                            'Impuesto': '002',
                            'TipoFactor': 'Tasa',
                            'TasaOCuota': Decimal('0.106667')
                        }
                    ]

                concepto_dict['Impuestos'] = impuestos_concepto

            conceptos.append(cfdi40.Concepto(**concepto_dict))

        # Build Comprobante with snake_case args for v4
        cfdi_kwargs = {
            'emisor': {
                'Rfc': 'TOSR520601AZ4',
                'RegimenFiscal': '612',
                'Nombre': 'RENE MANUEL TORTOLERO SANTILLANA'
            },
            'receptor': {
                'Rfc': invoice_data['receptor']['rfc'],
                'Nombre': sanitize_name(invoice_data['receptor']['nombre']),
                'UsoCFDI': invoice_data['receptor']['uso_cfdi'],
                'DomicilioFiscalReceptor': invoice_data['receptor']['domicilio_fiscal'],
                'RegimenFiscalReceptor': invoice_data['receptor'].get('regimen_fiscal', '601')
            },
            'conceptos': conceptos,
            'moneda': 'MXN',
            'tipo_de_comprobante': 'I',
            'lugar_expedicion': '28200',
            'exportacion': '01'
            # SubTotal, Total, Impuestos are omitted; satcfdi handles them
        }

        # Adding complemento if available
        if invoice_data.get('complemento_notarios'):
            from .complement_notarios import create_complemento_notarios
            from .api_models import ComplementoNotariosModel
            # Re-instantiate from dict to ensure validation
            comp_model = ComplementoNotariosModel(**invoice_data['complemento_notarios'])
            complemento = create_complemento_notarios(comp_model)
            if complemento:
                cfdi_kwargs['complemento'] = complemento

        cfdi = cfdi40.Comprobante(**cfdi_kwargs)

        # Signing
        signer = load_signer_from_secret_manager()
        if signer:
            cfdi.sign(signer)
        else:
            logger.info("No signer loaded. Returning unsigned XML.")

        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e

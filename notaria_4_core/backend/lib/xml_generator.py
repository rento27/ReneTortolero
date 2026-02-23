from decimal import Decimal
import logging
from typing import Dict, Any

try:
    from satcfdi.create.cfd import cfdi40
    from satcfdi.models import Signer
except ImportError:
    cfdi40 = None
    Signer = None

from .fiscal_engine import sanitize_name, IVA_RETENTION_RATE_DIRECT, ISR_RETENTION_RATE
from .complement_notarios import create_complemento_notarios
from .api_models import ComplementoNotariosModel

logger = logging.getLogger(__name__)

def generate_signed_xml(invoice_data: Dict[str, Any]) -> bytes:
    if not cfdi40:
        return b"<error>satcfdi not available</error>"

    receptor_rfc = invoice_data['receptor']['rfc']
    receptor_name = sanitize_name(invoice_data['receptor']['nombre'])
    is_moral = len(receptor_rfc) == 12

    conceptos = []
    for c in invoice_data['conceptos']:
        importe = Decimal(str(c['importe']))
        objeto_imp = c['objeto_imp']

        c_args = {
            'clave_prod_serv': c['clave_prod_serv'],
            'cantidad': Decimal(str(c['cantidad'])),
            'clave_unidad': c['clave_unidad'],
            'descripcion': c['descripcion'],
            'valor_unitario': Decimal(str(c['valor_unitario'])),
            'importe': importe,
            'objeto_imp': objeto_imp
        }

        if objeto_imp == '02':
            # Calculate Taxes per Concept
            traslados = []
            retenciones = []

            # IVA Traslado (16%)
            iva_tasa = Decimal('0.160000')
            iva_importe = (importe * iva_tasa).quantize(Decimal("0.01"))
            traslados.append({
                'Base': importe,
                'Impuesto': '002',
                'TipoFactor': 'Tasa',
                'TasaOCuota': iva_tasa,
                'Importe': iva_importe
            })

            if is_moral:
                # ISR Retention
                isr_importe = (importe * ISR_RETENTION_RATE).quantize(Decimal("0.01"))
                retenciones.append({
                    'Base': importe,
                    'Impuesto': '001',
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': ISR_RETENTION_RATE, # 0.10
                    'Importe': isr_importe
                })

                # IVA Retention
                iva_ret_importe = (importe * IVA_RETENTION_RATE_DIRECT).quantize(Decimal("0.01"))
                retenciones.append({
                    'Base': importe,
                    'Impuesto': '002',
                    'TipoFactor': 'Tasa',
                    'TasaOCuota': IVA_RETENTION_RATE_DIRECT, # 0.106667
                    'Importe': iva_ret_importe
                })

            impuestos_concept = {}
            if traslados:
                impuestos_concept['Traslados'] = traslados
            if retenciones:
                impuestos_concept['Retenciones'] = retenciones

            if impuestos_concept:
                c_args['impuestos'] = impuestos_concept

        conceptos.append(cfdi40.Concepto(**c_args))

    # Complemento
    complemento = None
    if invoice_data.get('complemento_notarios'):
        try:
            comp_model = ComplementoNotariosModel(**invoice_data['complemento_notarios'])
            complemento = create_complemento_notarios(comp_model)
        except Exception as e:
             raise ValueError(f"Invalid Complemento Notarios: {e}")

    try:
        cfdi = cfdi40.Comprobante(
            emisor={
                'Rfc': 'TOSR520601AZ4',
                'RegimenFiscal': '612',
                'Nombre': 'RENE MANUEL TORTOLERO SANTILLANA'
            },
            receptor={
                'Rfc': receptor_rfc,
                'Nombre': receptor_name,
                'UsoCFDI': invoice_data['receptor']['uso_cfdi'],
                'DomicilioFiscalReceptor': invoice_data['receptor']['domicilio_fiscal'],
                'RegimenFiscalReceptor': invoice_data['receptor']['regimen_fiscal']
            },
            conceptos=conceptos,
            moneda='MXN',
            tipo_de_comprobante='I',
            lugar_expedicion='28200',
            exportacion='01',
            complemento=complemento
        )

        return cfdi.xml_bytes()
    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e

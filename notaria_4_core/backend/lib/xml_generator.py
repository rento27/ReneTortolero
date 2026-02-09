from decimal import Decimal
import logging
import base64
import os

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import cfdi40
    from satcfdi.models import Signer
except ImportError:
    cfdi40 = None
    Signer = None

# Mock Google Cloud Secret Manager if not available
try:
    from google.cloud import secretmanager
except ImportError:
    secretmanager = None

from .fiscal_engine import validate_copropiedad, calculate_retentions
from .complement_notarios import create_complemento_notarios

logger = logging.getLogger(__name__)

def load_signer_from_secrets(project_id="notaria4", version="latest"):
    """
    Loads the Signer using keys from Google Secret Manager.
    Mocks the behavior if credentials are unavailable.
    """
    if not Signer:
        return None

    # In a real environment with GCP credentials:
    try:
        if secretmanager and os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            client = secretmanager.SecretManagerServiceClient()
            key_path = f"projects/{project_id}/secrets/csd-key/versions/{version}"
            cer_path = f"projects/{project_id}/secrets/csd-cer/versions/{version}"
            pass_path = f"projects/{project_id}/secrets/csd-pass/versions/{version}"

            key_bytes = client.access_secret_version(request={"name": key_path}).payload.data
            cer_bytes = client.access_secret_version(request={"name": cer_path}).payload.data
            password = client.access_secret_version(request={"name": pass_path}).payload.data.decode("utf-8")

            return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)
    except Exception as e:
        logger.warning(f"Could not load secrets from GCP: {e}")

    # Fallback/Mock for Dev/Test (No signing)
    logger.info("Using Mock Signer (No valid signature produced)")
    return None

def determine_objeto_imp(clave_prod_serv: str, description: str) -> str:
    """
    Determines ObjetoImp based on SAT rules.
    - 80131502 (Notarial Services) -> 02
    - Others (Suplidos, Derechos) -> 01
    """
    if clave_prod_serv == '80131502':
        return '02'

    desc_lower = description.lower()
    if any(k in desc_lower for k in ['suplido', 'derecho', 'traslado', 'inscripcion', 'registro']):
        return '01'

    return '01'

def generate_signed_xml(invoice_data: dict) -> bytes:
    """
    Generates a CFDI 4.0 XML object.
    Includes logic for Notarios Publicos complement.
    """

    if not cfdi40:
        logger.error("satcfdi library not found")
        return b"<error>satcfdi not available</error>"

    # 1. Pre-generation Validation (Coproperty Logic)
    if 'complemento_notarios' in invoice_data and invoice_data['complemento_notarios']:
        comp_data = invoice_data['complemento_notarios']

        # Validate Adquirientes Coproperty
        if 'datos_adquiriente' in comp_data and 'datos_adquirientes_cop_sc' in comp_data['datos_adquiriente']:
            copros = comp_data['datos_adquiriente']['datos_adquirientes_cop_sc']
            if copros:
                percentages = [Decimal(str(p['porcentaje'])) for p in copros]
                validate_copropiedad(percentages)

        # Validate Enajenantes Coproperty
        if 'datos_enajenante' in comp_data and 'datos_enajenantes_cop_sc' in comp_data['datos_enajenante']:
            copros = comp_data['datos_enajenante']['datos_enajenantes_cop_sc']
            if copros:
                percentages = [Decimal(str(p['porcentaje'])) for p in copros]
                validate_copropiedad(percentages)

    # 2. Build Taxes (Impuestos) & Concept Processing
    processed_concepts = []

    taxable_base = Decimal("0.00")

    for c in invoice_data['conceptos']:
        c_obj_imp = determine_objeto_imp(c['clave_prod_serv'], c['descripcion'])

        # Override based on Notarial Key
        if c['clave_prod_serv'] == '80131502':
            c_obj_imp = '02'

        cantidad = Decimal(str(c['cantidad']))
        valor_unitario = Decimal(str(c['valor_unitario']))
        importe = Decimal(str(c['importe']))

        concept_args = {
            'clave_prod_serv': c['clave_prod_serv'],
            'cantidad': cantidad,
            'clave_unidad': c['clave_unidad'],
            'descripcion': c['descripcion'],
            'valor_unitario': valor_unitario,
            'objeto_imp': c_obj_imp
        }

        if c_obj_imp == '02':
            base = importe
            taxable_base += base

            traslados_list = [
                cfdi40.Traslado(
                    base=base,
                    impuesto='002',
                    tipo_factor='Tasa',
                    tasa_o_cuota=Decimal('0.160000'),
                    importe=base * Decimal('0.16')
                )
            ]

            retenciones_list = []

            # Handle Retentions per Concept
            retentions = calculate_retentions(invoice_data['receptor']['rfc'], base)
            if retentions['is_moral']:
                # Add ISR
                retenciones_list.append(cfdi40.Retencion(
                    base=base,
                    impuesto='001', # ISR
                    tipo_factor='Tasa',
                    tasa_o_cuota=Decimal('0.100000'),
                    importe=retentions['isr']
                ))

                # Add IVA (10.6667%)
                retenciones_list.append(cfdi40.Retencion(
                    base=base,
                    impuesto='002', # IVA
                    tipo_factor='Tasa',
                    tasa_o_cuota=Decimal('0.106667'),
                    importe=retentions['iva']
                ))

            imp_args = {'traslados': traslados_list}
            if retenciones_list:
                imp_args['retenciones'] = retenciones_list

            concept_args['impuestos'] = cfdi40.Impuestos(**imp_args)

        processed_concepts.append(cfdi40.Concepto(**concept_args))

    # 4. Complemento Notarios
    complemento = None
    if 'complemento_notarios' in invoice_data and invoice_data['complemento_notarios']:
        complemento = create_complemento_notarios(invoice_data['complemento_notarios'])

    # 5. Construct Comprobante
    try:
        cfdi_args = {
            'emisor': cfdi40.Emisor(
                rfc='TOSR520601AZ4',
                regimen_fiscal='612',
                nombre='RENE MANUEL TORTOLERO SANTILLANA'
            ),
            'receptor': cfdi40.Receptor(
                rfc=invoice_data['receptor']['rfc'],
                nombre=invoice_data['receptor']['nombre'],
                uso_cfdi=invoice_data['receptor']['uso_cfdi'],
                domicilio_fiscal_receptor=invoice_data['receptor']['domicilio_fiscal'],
                regimen_fiscal_receptor=invoice_data['receptor']['regimen_fiscal']
            ),
            'conceptos': processed_concepts,
            'moneda': 'MXN',
            'tipo_de_comprobante': 'I',
            'lugar_expedicion': '28200',
            'exportacion': '01'
        }

        if complemento:
            cfdi_args['complemento'] = complemento

        cfdi = cfdi40.Comprobante(**cfdi_args)

        # 6. Signing
        signer = load_signer_from_secrets()
        if signer:
            cfdi.sign(signer)
        else:
            # If no signer, we return unsigned XML
            pass

        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        # Re-raise to let API handle it
        raise e

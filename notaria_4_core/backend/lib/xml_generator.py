from decimal import Decimal
import logging
import sys
import os
from .fiscal_engine import validate_copropiedad, calculate_retentions

logger = logging.getLogger(__name__)

# Check for satcfdi availability
try:
    from satcfdi.create.cfd import cfdi40
    from satcfdi.models import Signer
    # Import Notarios Publicos Complement
    from satcfdi.create.cfd.notariospublicos10 import (
        NotariosPublicos,
        DatosNotario as NP_DatosNotario,
        DatosOperacion as NP_DatosOperacion,
        DescInmueble as NP_DescInmueble,
        DatosAdquiriente as NP_DatosAdquiriente,
        DatosUnAdquiriente as NP_DatosUnAdquiriente,
        DatosAdquirienteCopSC as NP_DatosAdquirienteCopSC,
        DatosEnajenante as NP_DatosEnajenante,
        DatosUnEnajenante as NP_DatosUnEnajenante,
        DatosEnajenanteCopSC as NP_DatosEnajenanteCopSC
    )
except ImportError as e:
    logger.error(f"Import Error: {e}")
    cfdi40 = None
    Signer = None
    NotariosPublicos = None

# Check for Google Secret Manager availability
try:
    from google.cloud import secretmanager
except ImportError:
    secretmanager = None

# Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "notaria4")

def cargar_signer():
    """
    Loads the CSD (Certificate of Digital Seal) from Google Secret Manager.
    Returns a satcfdi.models.Signer object or None if unavailable.
    """
    if not secretmanager or not Signer:
        logger.warning("Secret Manager or Signer not available for signing.")
        return None

    try:
        client = secretmanager.SecretManagerServiceClient()
        # Retrieve secrets from GCP Secret Manager
        key_bytes = client.access_secret_version(request={"name": f"projects/{GCP_PROJECT_ID}/secrets/csd-key/versions/latest"}).payload.data
        cer_bytes = client.access_secret_version(request={"name": f"projects/{GCP_PROJECT_ID}/secrets/csd-cer/versions/latest"}).payload.data
        password = client.access_secret_version(request={"name": f"projects/{GCP_PROJECT_ID}/secrets/csd-pass/versions/latest"}).payload.data.decode("utf-8")

        return Signer.load(certificate=cer_bytes, key=key_bytes, password=password)
    except Exception as e:
        logger.error(f"Error loading signer from Secret Manager: {e}")
        return None

def generate_complemento_notarios(data: dict):
    """
    Generates the NotariosPublicos complement object.
    Expects 'data' to be the dictionary representation of ComplementoNotarios model.
    """
    if not NotariosPublicos:
        error_msg = "satcfdi.notariospublicos10 not available, cannot generate Complemento Notarios."
        logger.error(error_msg)
        raise ImportError(error_msg)

    # 1. Datos Notario
    dn_data = data['datos_notario']
    datos_notario = NP_DatosNotario(
        num_notaria=dn_data['num_notaria'],
        entidad_federativa=dn_data['entidad_federativa'],
        adscripcion=dn_data['adscripcion'],
        curp=dn_data['curp']
    )

    # 2. Datos Operacion
    do_data = data['datos_operacion']
    datos_operacion = NP_DatosOperacion(
        num_instrumento_notarial=do_data['num_instrumento_notarial'],
        fecha_inst_notarial=do_data['fecha_inst_notarial'],
        monto_operacion=Decimal(str(do_data['monto_operacion'])),
        subtotal=Decimal(str(do_data['subtotal'])),
        iva=Decimal(str(do_data['iva']))
    )

    # 3. Desc Inmueble
    di_data = data['desc_inmuebles']
    desc_inmuebles = NP_DescInmueble(
        tipo_inmueble=di_data['tipo_inmueble'],
        calle=di_data['calle'],
        no_exterior=di_data.get('no_exterior'),
        no_interior=di_data.get('no_interior'),
        colonia=di_data.get('colonia'),
        localidad=di_data.get('localidad'),
        referencia=di_data.get('referencia'),
        municipio=di_data['municipio'],
        estado=di_data['estado'],
        pais=di_data['pais'],
        codigo_postal=di_data['codigo_postal']
    )

    # 4. Datos Adquirientes
    is_copro = any(a['copro_soc_conyugal_e'] == 'Si' for a in data['datos_adquirientes'])

    if is_copro:
         cop_sc_list = []
         copro_percentages = []
         for adq in data['datos_adquirientes']:
             p = Decimal(str(adq['porcentaje'])) if adq.get('porcentaje') else Decimal('0')
             copro_percentages.append(p)
             cop_sc = NP_DatosAdquirienteCopSC(
                 nombre=adq['nombre'],
                 rfc=adq['rfc'],
                 porcentaje=p,
                 apellido_paterno=adq.get('apellido_paterno'),
                 apellido_materno=adq.get('apellido_materno'),
                 curp=adq.get('curp')
             )
             cop_sc_list.append(cop_sc)

         validate_copropiedad(copro_percentages)

         datos_adquirientes = NP_DatosAdquiriente(
             copro_soc_conyugal_e='Si',
             datos_adquirientes_cop_sc=cop_sc_list
         )
    else:
         # Non-Coproperty case
         un_adq_list = []
         for adq in data['datos_adquirientes']:
             un_adq = NP_DatosUnAdquiriente(
                 nombre=adq['nombre'],
                 rfc=adq['rfc'],
                 apellido_paterno=adq.get('apellido_paterno'),
                 apellido_materno=adq.get('apellido_materno'),
                 curp=adq.get('curp')
             )
             un_adq_list.append(un_adq)

         val = un_adq_list if len(un_adq_list) > 1 else un_adq_list[0]
         datos_adquirientes = NP_DatosAdquiriente(
             copro_soc_conyugal_e='No',
             datos_un_adquiriente=val
         )


    # 5. Datos Enajenantes
    datos_enajenantes = None
    if data.get('datos_enajenantes'):
        is_copro_ena = any(a['copro_soc_conyugal_e'] == 'Si' for a in data['datos_enajenantes'])

        if is_copro_ena:
             cop_sc_list_ena = []
             for ena in data['datos_enajenantes']:
                 # Logic for EnajenanteCopSC
                 p_ena = Decimal(str(ena['porcentaje'])) if ena.get('porcentaje') else Decimal('0')
                 cop_sc_ena = NP_DatosEnajenanteCopSC(
                     nombre=ena['nombre'],
                     rfc=ena['rfc'],
                     porcentaje=p_ena,
                     apellido_paterno=ena.get('apellido_paterno'),
                     apellido_materno=ena.get('apellido_materno'),
                     curp=ena.get('curp')
                 )
                 cop_sc_list_ena.append(cop_sc_ena)

             datos_enajenantes = NP_DatosEnajenante(
                 copro_soc_conyugal_e='Si',
                 datos_enajenantes_cop_sc=cop_sc_list_ena
             )
        else:
             un_ena_list = []
             for ena in data['datos_enajenantes']:
                 un_ena = NP_DatosUnEnajenante(
                     nombre=ena['nombre'],
                     rfc=ena['rfc'],
                     apellido_paterno=ena.get('apellido_paterno'),
                     apellido_materno=ena.get('apellido_materno'),
                     curp=ena.get('curp')
                 )
                 un_ena_list.append(un_ena)

             val_ena = un_ena_list if len(un_ena_list) > 1 else un_ena_list[0]
             datos_enajenantes = NP_DatosEnajenante(
                 copro_soc_conyugal_e='No',
                 datos_un_enajenante=val_ena
             )

    # 6. Build Complement
    return NotariosPublicos(
        datos_notario=datos_notario,
        datos_operacion=datos_operacion,
        desc_inmuebles=desc_inmuebles,
        datos_adquiriente=datos_adquirientes,
        datos_enajenante=datos_enajenantes
    )

def generate_signed_xml(invoice_data: dict) -> bytes:
    """
    Generates a CFDI 4.0 XML object.
    Attempts to sign it using credentials from Secret Manager.
    Returns the XML bytes (signed or unsigned).
    """

    if not cfdi40:
        logger.error("satcfdi library not found")
        raise ImportError("satcfdi library not available")

    # 2. Build Taxes (Impuestos)
    impuestos = None
    retentions = calculate_retentions(invoice_data['receptor']['rfc'], Decimal(str(invoice_data['subtotal'])))

    if retentions['is_moral']:
        # Construct Impuestos node
        impuestos = cfdi40.Impuestos(
            Retenciones=[
                cfdi40.Retencion(Impuesto='001', Importe=retentions['isr']), # ISR
                cfdi40.Retencion(Impuesto='002', Importe=retentions['iva'])  # IVA
            ]
        )

    # 3. Construct Comprobante
    try:
        # Build Complement if data exists
        complemento = None
        if invoice_data.get('complemento_notarios'):
             complemento = generate_complemento_notarios(invoice_data['complemento_notarios'])

        cfdi = cfdi40.Comprobante(
            Emisor={
                'Rfc': 'TOSR520601AZ4',
                'RegimenFiscal': '612',
                'Nombre': 'RENE MANUEL TORTOLERO SANTILLANA'
            },
            Receptor={
                'Rfc': invoice_data['receptor']['rfc'],
                'Nombre': invoice_data['receptor']['nombre'],
                'UsoCFDI': invoice_data['receptor']['uso_cfdi'],
                'DomicilioFiscalReceptor': invoice_data['receptor']['domicilio_fiscal'],
                'RegimenFiscalReceptor': invoice_data['receptor']['regimen_fiscal']
            },
            Conceptos=[
                {
                    'ClaveProdServ': c['clave_prod_serv'],
                    'Cantidad': Decimal(str(c['cantidad'])),
                    'ClaveUnidad': c['clave_unidad'],
                    'Descripcion': c['descripcion'],
                    'ValorUnitario': Decimal(str(c['valor_unitario'])),
                    'Importe': Decimal(str(c['importe'])),
                    'ObjetoImp': c['objeto_imp'],
                } for c in invoice_data['conceptos']
            ],
            SubTotal=Decimal(str(invoice_data['subtotal'])),
            Moneda='MXN',
            Total=Decimal(str(invoice_data['total'])),
            TipoDeComprobante='I',
            LugarExpedicion='28200',
            Impuestos=impuestos,
            Exportacion='01',
            Complemento=complemento
        )

        # 5. Signing
        signer = cargar_signer()
        if signer:
            try:
                cfdi.sign(signer)
            except Exception as e:
                logger.error(f"Error signing CFDI: {e}")
        else:
             logger.warning("CFDI generated without signature (Signer not available)")

        # Return the XML structure
        return cfdi.xml_bytes()

    except Exception as e:
        logger.error(f"Error generating CFDI: {e}")
        raise e

from decimal import Decimal
from datetime import date
from .api_models import ComplementoNotariosModel, DatosAdquirienteModel, DatosEnajenanteModel
from .fiscal_engine import validate_copropiedad
from satcfdi.create.cfd.notariospublicos10 import (
    NotariosPublicos, DatosNotario, DatosOperacion, DescInmueble,
    DatosAdquiriente, DatosAdquirienteCopSC, DatosUnAdquiriente,
    DatosEnajenante, DatosEnajenanteCopSC, DatosUnEnajenante
)

# Constants for Notaria 4
NUM_NOTARIA_DEFAULT = 4
ENTIDAD_FEDERATIVA_DEFAULT = "06"
ADSCRIPCION_DEFAULT = "MANZANILLO COLIMA"
CURP_NOTARIO_FALLBACK = "TOSR520601HOCMXA00" # Lic. René Manuel Tortolero Santillana (inferred)

def create_complemento_notarios(data: ComplementoNotariosModel) -> NotariosPublicos:
    """
    Creates the NotariosPublicos complement object from the input model.
    """

    # 1. DatosNotario
    dn_model = data.datos_notario
    datos_notario = DatosNotario(
        curp=dn_model.curp if dn_model and dn_model.curp else CURP_NOTARIO_FALLBACK,
        num_notaria=dn_model.num_notaria if dn_model else NUM_NOTARIA_DEFAULT,
        entidad_federativa=dn_model.entidad_federativa if dn_model else ENTIDAD_FEDERATIVA_DEFAULT,
        adscripcion=dn_model.adscripcion if dn_model else ADSCRIPCION_DEFAULT
    )

    # 2. DatosOperacion
    do_model = data.datos_operacion

    if do_model.fecha_inst_notarial > date.today():
        raise ValueError(f"FechaInstNotarial cannot be in the future: {do_model.fecha_inst_notarial}")

    datos_operacion = DatosOperacion(
        num_instrumento_notarial=do_model.num_instrumento_notarial,
        fecha_inst_notarial=do_model.fecha_inst_notarial,
        monto_operacion=do_model.monto_operacion,
        subtotal=do_model.subtotal,
        iva=do_model.iva
    )

    # 3. DescInmuebles
    inmuebles = []
    for inm in data.inmuebles:
        inmuebles.append(DescInmueble(
            tipo_inmueble=inm.tipo_inmueble,
            calle=inm.calle,
            no_exterior=inm.no_exterior,
            no_interior=inm.no_interior,
            colonia=inm.colonia,
            localidad=inm.localidad,
            referencia=inm.referencia,
            municipio=inm.municipio,
            estado=inm.estado,
            pais=inm.pais,
            codigo_postal=inm.codigo_postal
        ))

    # 4. DatosAdquirientes
    datos_adquirientes = process_adquirientes(data.adquirientes)

    # 5. DatosEnajenantes
    datos_enajenantes = process_enajenantes(data.enajenantes)

    # Construct the complement
    # satcfdi automatically handles the wrapping if args match,
    # but we will be explicit with keyword arguments for clarity and safety.
    return NotariosPublicos(
        datos_notario=datos_notario,
        datos_operacion=datos_operacion,
        desc_inmuebles=inmuebles,
        datos_adquiriente=datos_adquirientes,
        datos_enajenante=datos_enajenantes
    )

def process_adquirientes(adquirientes_list: list[DatosAdquirienteModel]):
    if not adquirientes_list:
        return None

    has_copro = any(a.copro_soc_conyugal_e == 'Si' for a in adquirientes_list)

    if has_copro:
        percentages = [a.porcentaje for a in adquirientes_list if a.porcentaje is not None]
        if len(percentages) != len(adquirientes_list):
             # Logic gap: What if percentage is missing? Assuming required for copro.
             raise ValueError("All acquirers must have a percentage defined in coproperty mode.")

        validate_copropiedad(percentages)

        cop_list = []
        for a in adquirientes_list:
            cop_list.append(DatosAdquirienteCopSC(
                nombre=a.nombre,
                apellido_paterno=a.apellido_paterno,
                apellido_materno=a.apellido_materno,
                rfc=a.rfc,
                curp=a.curp,
                porcentaje=a.porcentaje
            ))

        return DatosAdquiriente(
            copro_soc_conyugal_e='Si',
            datos_adquirientes_cop_sc=cop_list
        )

    else:
        if len(adquirientes_list) > 1:
             raise ValueError("Multiple acquirers found but CoproSocConyugalE is 'No'. Set to 'Si' for coproperty.")

        a = adquirientes_list[0]
        un_adq = DatosUnAdquiriente(
            nombre=a.nombre,
            apellido_paterno=a.apellido_paterno,
            apellido_materno=a.apellido_materno,
            rfc=a.rfc,
            curp=a.curp
        )
        return DatosAdquiriente(
            copro_soc_conyugal_e='No',
            datos_un_adquiriente=un_adq
        )

def process_enajenantes(enajenantes_list: list[DatosEnajenanteModel]):
    if not enajenantes_list:
        return None

    has_copro = any(a.copro_soc_conyugal_e == 'Si' for a in enajenantes_list)

    if has_copro:
        percentages = [a.porcentaje for a in enajenantes_list if a.porcentaje is not None]
        if len(percentages) != len(enajenantes_list):
             raise ValueError("All alienators must have a percentage defined in coproperty mode.")
        validate_copropiedad(percentages)

        cop_list = []
        for a in enajenantes_list:
            cop_list.append(DatosEnajenanteCopSC(
                nombre=a.nombre,
                apellido_paterno=a.apellido_paterno,
                apellido_materno=a.apellido_materno,
                rfc=a.rfc,
                curp=a.curp,
                porcentaje=a.porcentaje
            ))

        return DatosEnajenante(
            copro_soc_conyugal_e='Si',
            datos_enajenantes_cop_sc=cop_list
        )

    else:
        if len(enajenantes_list) > 1:
             raise ValueError("Multiple alienators found but CoproSocConyugalE is 'No'. Set to 'Si' for coproperty.")

        a = enajenantes_list[0]
        un_ena = DatosUnEnajenante(
            nombre=a.nombre,
            apellido_paterno=a.apellido_paterno,
            apellido_materno=a.apellido_materno,
            rfc=a.rfc,
            curp=a.curp
        )
        return DatosEnajenante(
            copro_soc_conyugal_e='No',
            datos_un_enajenante=un_ena
        )

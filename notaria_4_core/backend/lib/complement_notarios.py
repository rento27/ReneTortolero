from decimal import Decimal
from typing import List, Dict, Any
from .api_models import ComplementoNotariosModel, DatosAdquiriente as AdquirienteModel, DatosEnajenante as EnajenanteModel
from .fiscal_engine import validate_copropiedad, sanitize_name

try:
    from satcfdi.create.cfd.notariospublicos10 import NotariosPublicos, DatosOperacion, DescInmueble
    from satcfdi.create.cfd.notariospublicos10 import DatosAdquiriente, DatosUnAdquiriente, DatosAdquirienteCopSC
    from satcfdi.create.cfd.notariospublicos10 import DatosEnajenante, DatosUnEnajenante, DatosEnajenanteCopSC
    from satcfdi.create.cfd.notariospublicos10 import DatosNotario
except ImportError:
    NotariosPublicos = None

def create_complemento_notarios(data: ComplementoNotariosModel):
    if not NotariosPublicos:
        raise ImportError("satcfdi library is not installed or notariospublicos10 module missing")

    # 1. DatosNotario
    datos_notario = DatosNotario(
        curp=data.datos_notario.curp,
        num_notaria=data.datos_notario.num_notaria,
        entidad_federativa=data.datos_notario.entidad_federativa,
        adscripcion=data.datos_notario.adscripcion
    )

    # 2. DatosOperacion
    datos_operacion = DatosOperacion(
        num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=data.datos_operacion.fecha_inst_notarial,
        monto_operacion=data.datos_operacion.monto_operacion,
        subtotal=data.datos_operacion.subtotal,
        iva=data.datos_operacion.iva
    )

    # 3. DescInmuebles
    # satcfdi automatically handles the wrapping if we pass a list of DescInmueble to NotariosPublicos
    desc_inmuebles = []
    for inmueble in data.desc_inmuebles:
        desc_inmuebles.append(DescInmueble(
            tipo_inmueble=inmueble.tipo_inmueble,
            calle=inmueble.calle,
            no_exterior=inmueble.no_exterior,
            no_interior=inmueble.no_interior,
            colonia=inmueble.colonia,
            localidad=inmueble.localidad,
            referencia=inmueble.referencia,
            municipio=inmueble.municipio,
            estado=inmueble.estado,
            pais=inmueble.pais,
            codigo_postal=inmueble.codigo_postal
        ))

    # 4. DatosAdquiriente Logic
    adquiriente_node = None
    adquirientes = data.datos_adquirientes

    if len(adquirientes) == 1 and adquirientes[0].copro_soc_conyugal_e == 'No':
        # Single acquirer, no coproperty
        a = adquirientes[0]
        adquiriente_node = DatosAdquiriente(
            copro_soc_conyugal_e='No',
            datos_un_adquiriente=DatosUnAdquiriente(
                nombre=sanitize_name(a.nombre),
                rfc=a.rfc,
                curp=a.curp,
                apellido_paterno=a.apellido_paterno,
                apellido_materno=a.apellido_materno
            )
        )
    else:
        # Coproperty or multiple acquirers
        # Validate percentages sum to 100
        percentages = [a.porcentaje for a in adquirientes if a.porcentaje is not None]
        if percentages:
            validate_copropiedad(percentages)

        cop_list = []
        for a in adquirientes:
             cop_list.append(DatosAdquirienteCopSC(
                nombre=sanitize_name(a.nombre),
                rfc=a.rfc,
                curp=a.curp,
                porcentaje=a.porcentaje,
                apellido_paterno=a.apellido_paterno,
                apellido_materno=a.apellido_materno
             ))

        adquiriente_node = DatosAdquiriente(
            copro_soc_conyugal_e='Si',
            datos_adquirientes_cop_sc=cop_list
        )

    # 5. DatosEnajenante Logic
    enajenante_node = None
    enajenantes = data.datos_enajenantes

    if len(enajenantes) == 1 and enajenantes[0].copro_soc_conyugal_e == 'No':
        # Single seller, no coproperty
        e = enajenantes[0]
        enajenante_node = DatosEnajenante(
            copro_soc_conyugal_e='No',
            datos_un_enajenante=DatosUnEnajenante(
                nombre=sanitize_name(e.nombre),
                rfc=e.rfc,
                curp=e.curp,
                apellido_paterno=e.apellido_paterno,
                apellido_materno=e.apellido_materno
            )
        )
    else:
        # Coproperty or multiple sellers
        percentages = [e.porcentaje for e in enajenantes if e.porcentaje is not None]
        if percentages:
            validate_copropiedad(percentages)

        cop_list = []
        for e in enajenantes:
            cop_list.append(DatosEnajenanteCopSC(
                nombre=sanitize_name(e.nombre),
                rfc=e.rfc,
                curp=e.curp,
                porcentaje=e.porcentaje,
                apellido_paterno=e.apellido_paterno,
                apellido_materno=e.apellido_materno
            ))

        enajenante_node = DatosEnajenante(
            copro_soc_conyugal_e='Si',
            datos_enajenantes_cop_sc=cop_list
        )

    # 6. Assemble Complement
    complemento = NotariosPublicos(
        datos_notario=datos_notario,
        datos_operacion=datos_operacion,
        desc_inmuebles=desc_inmuebles,
        datos_adquiriente=adquiriente_node,
        datos_enajenante=enajenante_node
    )

    return complemento

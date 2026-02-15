from decimal import Decimal
from typing import List, Union
from .api_models import ComplementoNotariosModel, DatosAdquiriente as DatosAdquirienteModel, DatosEnajenante as DatosEnajenanteModel

try:
    from satcfdi.create.cfd.notariospublicos10 import NotariosPublicos, DatosNotario, DatosOperacion, \
        DescInmueble, DatosAdquiriente, DatosUnAdquiriente, DatosAdquirienteCopSC, \
        DatosEnajenante, DatosUnEnajenante, DatosEnajenanteCopSC
except ImportError:
    NotariosPublicos = None

DEFAULT_NOTARY_CURP = "TOSR520601HOCMXA00"

def split_name_fallback(nombre_full: str):
    """
    Splits a full name into Nombre, ApellidoPaterno, ApellidoMaterno.
    """
    parts = nombre_full.strip().split()
    if len(parts) >= 3:
        materno = parts[-1]
        paterno = parts[-2]
        nombre = " ".join(parts[:-2])
        return nombre, paterno, materno
    elif len(parts) == 2:
        return parts[0], parts[1], None
    return nombre_full, None, None

def validate_percentages(items: List[Union[DatosAdquirienteModel, DatosEnajenanteModel]], role: str):
    """
    Validates that percentages sum to 100% for coproperties.
    """
    for item in items:
        if item.copropietarios:
            total = sum(c.porcentaje for c in item.copropietarios)
            if total != Decimal("100.00"):
                raise ValueError(f"Sum of percentages for {role} {item.nombre} must be 100.00%, got {total}")

def create_complemento_notarios(data: ComplementoNotariosModel):
    if not NotariosPublicos:
        raise ImportError("satcfdi library not found")

    # 1. DatosNotario
    notario_curp = data.datos_notario.curp or DEFAULT_NOTARY_CURP
    notario = DatosNotario(
        curp=notario_curp,
        num_notaria=data.datos_notario.num_notaria,
        entidad_federativa=data.datos_notario.entidad_federativa,
        adscripcion=data.datos_notario.adscripcion
    )

    # 2. DatosOperacion
    operacion = DatosOperacion(
        num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=data.datos_operacion.fecha_inst_notarial,
        monto_operacion=data.datos_operacion.monto_operacion,
        subtotal=data.datos_operacion.subtotal,
        iva=data.datos_operacion.iva
    )

    # 3. DescInmuebles (List)
    desc_inmueble = DescInmueble(
        tipo_inmueble=data.datos_inmueble.tipo_inmueble,
        calle=data.datos_inmueble.calle,
        no_exterior=data.datos_inmueble.no_exterior,
        no_interior=data.datos_inmueble.no_interior,
        colonia=data.datos_inmueble.colonia,
        localidad=data.datos_inmueble.localidad,
        referencia=data.datos_inmueble.referencia,
        municipio=data.datos_inmueble.municipio,
        estado=data.datos_inmueble.estado,
        pais=data.datos_inmueble.pais,
        codigo_postal=data.datos_inmueble.codigo_postal
    )
    desc_inmuebles_list = [desc_inmueble]

    # 4. DatosAdquiriente (Singular in satcfdi, corresponds to DatosAdquirientes element)
    # We take the first item from the list in API model
    if not data.datos_adquirientes:
        raise ValueError("At least one DatosAdquiriente is required")

    adq_model = data.datos_adquirientes[0]
    validate_percentages(data.datos_adquirientes, "Adquiriente")

    datos_un_adquiriente = None
    datos_adquirientes_cop_sc = None

    if adq_model.copro_soc_conyugal_e == 'No':
        # Single Buyer logic
        nombre_a, pat_a, mat_a = adq_model.nombre, adq_model.apellido_paterno, adq_model.apellido_materno
        if not pat_a:
             nombre_a, pat_a, mat_a = split_name_fallback(adq_model.nombre)

        datos_un_adquiriente = DatosUnAdquiriente(
            nombre=nombre_a,
            apellido_paterno=pat_a,
            apellido_materno=mat_a,
            rfc=adq_model.rfc,
            curp=adq_model.curp
        )
    else:
        # Coproperty logic
        datos_adquirientes_cop_sc = []
        if adq_model.copropietarios:
            for c in adq_model.copropietarios:
                nombre_c, pat_c, mat_c = c.nombre, c.apellido_paterno, c.apellido_materno
                if not pat_c:
                     nombre_c, pat_c, mat_c = split_name_fallback(c.nombre)

                datos_adquirientes_cop_sc.append(DatosAdquirienteCopSC(
                    nombre=nombre_c,
                    apellido_paterno=pat_c,
                    apellido_materno=mat_c,
                    rfc=c.rfc,
                    curp=c.curp,
                    porcentaje=c.porcentaje
                ))

    datos_adquiriente = DatosAdquiriente(
        copro_soc_conyugal_e=adq_model.copro_soc_conyugal_e,
        datos_un_adquiriente=datos_un_adquiriente,
        datos_adquirientes_cop_sc=datos_adquirientes_cop_sc
    )

    # 5. DatosEnajenante
    datos_enajenante = None
    if data.datos_enajenantes:
        validate_percentages(data.datos_enajenantes, "Enajenante")
        ena_model = data.datos_enajenantes[0]

        datos_un_enajenante = None
        datos_enajenantes_cop_sc = None

        if ena_model.copro_soc_conyugal_e == 'No':
            nombre_e, pat_e, mat_e = ena_model.nombre, ena_model.apellido_paterno, ena_model.apellido_materno
            if not pat_e:
                nombre_e, pat_e, mat_e = split_name_fallback(ena_model.nombre)

            datos_un_enajenante = DatosUnEnajenante(
                nombre=nombre_e,
                apellido_paterno=pat_e,
                apellido_materno=mat_e,
                rfc=ena_model.rfc,
                curp=ena_model.curp
            )
        else:
             datos_enajenantes_cop_sc = []
             if ena_model.copropietarios:
                for c in ena_model.copropietarios:
                    nombre_c, pat_c, mat_c = c.nombre, c.apellido_paterno, c.apellido_materno
                    if not pat_c:
                        nombre_c, pat_c, mat_c = split_name_fallback(c.nombre)

                    datos_enajenantes_cop_sc.append(DatosEnajenanteCopSC(
                        nombre=nombre_c,
                        apellido_paterno=pat_c,
                        apellido_materno=mat_c,
                        rfc=c.rfc,
                        curp=c.curp,
                        porcentaje=c.porcentaje
                    ))

        datos_enajenante = DatosEnajenante(
            copro_soc_conyugal_e=ena_model.copro_soc_conyugal_e,
            datos_un_enajenante=datos_un_enajenante,
            datos_enajenantes_cop_sc=datos_enajenantes_cop_sc
        )

    return NotariosPublicos(
        datos_notario=notario,
        datos_operacion=operacion,
        desc_inmuebles=desc_inmuebles_list,
        datos_adquiriente=datos_adquiriente,
        datos_enajenante=datos_enajenante
    )

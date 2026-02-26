from datetime import date
from decimal import Decimal
from typing import List, Tuple
from satcfdi.create.cfd.notariospublicos10 import (
    NotariosPublicos, DatosNotario, DatosOperacion, DescInmueble,
    DatosAdquiriente, DatosAdquirienteCopSC, DatosUnAdquiriente,
    DatosEnajenante, DatosEnajenanteCopSC, DatosUnEnajenante
)
from .api_models import ComplementoNotariosModel
from .fiscal_engine import validate_copropiedad

# Constants for Notaria 4
NUM_NOTARIA = 4
ENTIDAD_FEDERATIVA = "06" # Colima
ADSCRIPCION = "MANZANILLO COLIMA"

def split_name(full_name: str) -> Tuple[str, str, str]:
    """
    Splits a full name into Name, Paternal Surname, Maternal Surname.
    Simple heuristic: Last 2 words are surnames, rest is name.
    """
    parts = full_name.strip().split()
    if len(parts) < 3:
        # Fallback for short names: Name is first, Paternal is last, Maternal empty
        if len(parts) == 2:
            return parts[0], parts[1], ""
        if len(parts) == 1:
            return parts[0], "", ""
        return "", "", ""

    return " ".join(parts[:-2]), parts[-2], parts[-1]

def create_complemento_notarios(data: ComplementoNotariosModel) -> NotariosPublicos:
    # 1. Validate Date
    if data.datos_operacion.fecha_inst_notarial > date.today():
        raise ValueError(f"FechaInstNotarial cannot be in the future: {data.datos_operacion.fecha_inst_notarial}")

    # 2. Build DatosAdquirientes
    adquirientes_node = []

    # Determine if Copropiedad
    is_copro = len(data.datos_adquirientes) > 1
    # Check if explicit flag is set on any
    for a in data.datos_adquirientes:
        if a.copro_soc_conyugal_e == "Si":
            is_copro = True
            break

    if is_copro:
        # Validate Percentages
        percentages = [a.porcentaje for a in data.datos_adquirientes if a.porcentaje is not None]

        # If percentages provided, validate sum
        if percentages:
            validate_copropiedad(percentages)

        cop_sc_list = []
        for a in data.datos_adquirientes:
            nom, pat, mat = split_name(a.nombre)
            cop_sc_list.append(DatosAdquirienteCopSC(
                nombre=nom,
                apellido_paterno=a.apellido_paterno or pat,
                apellido_materno=a.apellido_materno or mat,
                rfc=a.rfc,
                curp=a.curp, # Mandatory for Adquiriente? XSD says Optional but prompt implies strictness
                porcentaje=a.porcentaje
            ))

        adquirientes_node.append(DatosAdquiriente(
            copro_soc_conyugal_e="Si",
            datos_adquirientes_cop_sc=cop_sc_list
        ))
    else:
        # Single Adquiriente
        if data.datos_adquirientes:
            a = data.datos_adquirientes[0]
            nom, pat, mat = split_name(a.nombre)
            adquirientes_node.append(DatosAdquiriente(
                copro_soc_conyugal_e="No",
                datos_un_adquiriente=DatosUnAdquiriente(
                    nombre=nom,
                    apellido_paterno=a.apellido_paterno or pat,
                    apellido_materno=a.apellido_materno or mat,
                    rfc=a.rfc,
                    curp=a.curp
                )
            ))

    # 3. Build DatosEnajenantes (Similar logic)
    enajenantes_node = []
    is_copro_enaj = len(data.datos_enajenantes) > 1
    for e in data.datos_enajenantes:
         if e.copro_soc_conyugal_e == "Si":
            is_copro_enaj = True
            break

    if is_copro_enaj:
        percentages = [e.porcentaje for e in data.datos_enajenantes if e.porcentaje is not None]
        if percentages:
            validate_copropiedad(percentages)

        cop_sc_list = []
        for e in data.datos_enajenantes:
            nom, pat, mat = split_name(e.nombre)
            cop_sc_list.append(DatosEnajenanteCopSC(
                nombre=nom,
                apellido_paterno=e.apellido_paterno or pat,
                apellido_materno=e.apellido_materno or mat,
                rfc=e.rfc,
                curp=e.curp,
                porcentaje=e.porcentaje
            ))
        enajenantes_node.append(DatosEnajenante(
            copro_soc_conyugal_e="Si",
            datos_enajenantes_cop_sc=cop_sc_list
        ))
    else:
        if data.datos_enajenantes:
            e = data.datos_enajenantes[0]
            nom, pat, mat = split_name(e.nombre)
            enajenantes_node.append(DatosEnajenante(
                copro_soc_conyugal_e="No",
                datos_un_enajenante=DatosUnEnajenante(
                    nombre=nom,
                    apellido_paterno=e.apellido_paterno or pat,
                    apellido_materno=e.apellido_materno or mat,
                    rfc=e.rfc,
                    curp=e.curp
                )
            ))

    # 4. Build DescInmuebles
    inmuebles = [
        DescInmueble(
            tipo_inmueble=i.tipo_inmueble,
            calle=i.calle,
            no_exterior=i.no_exterior,
            no_interior=i.no_interior,
            colonia=i.colonia,
            localidad=i.localidad,
            municipio=i.municipio,
            estado=i.entidad_federativa,
            pais=i.pais,
            codigo_postal=i.codigo_postal
        ) for i in data.desc_inmuebles
    ]

    # 5. Build NotariosPublicos
    # satcfdi v4 expects singular objects for datos_adquiriente/enajenante
    # We assume all inputs belong to a single grouping (either UnAdquiriente or CopSC)
    return NotariosPublicos(
        datos_notario=DatosNotario(
            curp=data.datos_notario.curp_notario,
            num_notaria=NUM_NOTARIA,
            entidad_federativa=ENTIDAD_FEDERATIVA,
            adscripcion=ADSCRIPCION
        ),
        datos_operacion=DatosOperacion(
            num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
            fecha_inst_notarial=data.datos_operacion.fecha_inst_notarial,
            monto_operacion=data.datos_operacion.monto_operacion,
            subtotal=data.datos_operacion.subtotal,
            iva=data.datos_operacion.iva
        ),
        datos_adquiriente=adquirientes_node[0] if adquirientes_node else None,
        datos_enajenante=enajenantes_node[0] if enajenantes_node else None,
        desc_inmuebles=inmuebles
    )

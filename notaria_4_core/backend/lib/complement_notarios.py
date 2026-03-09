import datetime
import logging
from typing import List, Tuple, Dict
from decimal import Decimal

from satcfdi.create.cfd.notariospublicos10 import (
    NotariosPublicos,
    DatosNotario,
    DatosOperacion,
    DatosEnajenante,
    DatosEnajenanteCopSC,
    DatosUnEnajenante,
    DatosAdquiriente,
    DatosAdquirienteCopSC,
    DatosUnAdquiriente,
    DescInmueble
)
from .fiscal_engine import sanitize_name

logger = logging.getLogger(__name__)

def split_name(full_name: str) -> Tuple[str, str, str]:
    """
    Fallback mechanism to generate Nombre, ApellidoPaterno, and ApellidoMaterno.
    Returns (full_name, '', '') for single-word inputs to avoid ambiguous assignments.
    """
    parts = full_name.split()
    if len(parts) <= 1:
        return full_name, '', ''
    elif len(parts) == 2:
        return parts[0], parts[1], ''
    else:
        # Assumes last two words are paternal and maternal surnames
        nombre = " ".join(parts[:-2])
        return nombre, parts[-2], parts[-1]

def create_complemento_notarios(data: 'ComplementoNotariosModel') -> NotariosPublicos:
    """
    Creates and validates the NotariosPublicos v4 complement.
    Applies strict validation rules per requirements.
    """

    datos_notario = DatosNotario(
        curp=data.datos_notario.curp or 'TOSR520601HOCMXA00',
        num_notaria=4,
        entidad_federativa='06',
        adscripcion='MANZANILLO'
    )

    # 2. Validate FechaInstNotarial
    fecha_inst = datetime.datetime.fromisoformat(data.datos_operacion.fecha_inst_notarial).date()
    if fecha_inst > datetime.date.today():
        raise ValueError("FechaInstNotarial cannot be in the future")

    datos_operacion = DatosOperacion(
        num_instrumento_notarial=data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=fecha_inst,
        monto_operacion=data.datos_operacion.monto_operacion,
        subtotal=data.datos_operacion.subtotal,
        iva=data.datos_operacion.iva
    )

    # 3. Enajenantes
    def map_enajenante_un(e):
        ap, am, nm = e.apellido_paterno, e.apellido_materno, e.nombre
        if not ap and not am:
            nm, ap, am = split_name(e.nombre)
        return DatosUnEnajenante(
            nombre=sanitize_name(nm),
            apellido_paterno=sanitize_name(ap) if ap else None,
            apellido_materno=sanitize_name(am) if am else None,
            rfc=e.rfc,
            curp=e.curp
        )

    def map_enajenante_cop(e):
        ap, am, nm = e.apellido_paterno, e.apellido_materno, e.nombre
        if not ap and not am:
            nm, ap, am = split_name(e.nombre)
        return DatosEnajenanteCopSC(
            nombre=sanitize_name(nm),
            apellido_paterno=sanitize_name(ap) if ap else None,
            apellido_materno=sanitize_name(am) if am else None,
            rfc=e.rfc,
            curp=e.curp,
            porcentaje=e.porcentaje
        )

    if not data.datos_enajenantes:
        raise ValueError("At least one enajenante is required")

    is_copro_enaj = data.datos_enajenantes[0].copro_soc_conyugal_e == 'Si'

    if not is_copro_enaj and len(data.datos_enajenantes) > 1:
        raise ValueError("If CoproSocConyugalE is 'No', the list of enajenantes must contain exactly one item.")

    if is_copro_enaj:
         porcentajes = [e.porcentaje for e in data.datos_enajenantes if e.porcentaje is not None]
         if sum(porcentajes) != Decimal('100.00'):
             raise ValueError("Coproperty percentages for Enajenantes must sum exactly to 100.00")

         datos_enajenante_obj = DatosEnajenante(
              copro_soc_conyugal_e='Si',
              datos_enajenantes_cop_sc=[map_enajenante_cop(e) for e in data.datos_enajenantes]
         )
    else:
         datos_enajenante_obj = DatosEnajenante(
              copro_soc_conyugal_e='No',
              datos_un_enajenante=map_enajenante_un(data.datos_enajenantes[0])
         )

    # 4. Adquirientes
    def map_adquiriente_un(a):
        ap, am, nm = a.apellido_paterno, a.apellido_materno, a.nombre
        if not ap and not am:
             nm, ap, am = split_name(a.nombre)
        return DatosUnAdquiriente(
             nombre=sanitize_name(nm),
             apellido_paterno=sanitize_name(ap) if ap else None,
             apellido_materno=sanitize_name(am) if am else None,
             rfc=a.rfc,
             curp=a.curp
        )

    def map_adquiriente_cop(a):
        ap, am, nm = a.apellido_paterno, a.apellido_materno, a.nombre
        if not ap and not am:
             nm, ap, am = split_name(a.nombre)
        return DatosAdquirienteCopSC(
             nombre=sanitize_name(nm),
             apellido_paterno=sanitize_name(ap) if ap else None,
             apellido_materno=sanitize_name(am) if am else None,
             rfc=a.rfc,
             curp=a.curp,
             porcentaje=a.porcentaje
        )

    if not data.datos_adquirientes:
        raise ValueError("At least one adquiriente is required")

    is_copro_adq = data.datos_adquirientes[0].copro_soc_conyugal_e == 'Si'

    if not is_copro_adq and len(data.datos_adquirientes) > 1:
        raise ValueError("If CoproSocConyugalE is 'No', the list of adquirientes must contain exactly one item.")

    if is_copro_adq:
         porcentajes = [a.porcentaje for a in data.datos_adquirientes if a.porcentaje is not None]
         if sum(porcentajes) != Decimal('100.00'):
             raise ValueError("Coproperty percentages for Adquirientes must sum exactly to 100.00")

         datos_adquiriente_obj = DatosAdquiriente(
              copro_soc_conyugal_e='Si',
              datos_adquirientes_cop_sc=[map_adquiriente_cop(a) for a in data.datos_adquirientes]
         )
    else:
         datos_adquiriente_obj = DatosAdquiriente(
              copro_soc_conyugal_e='No',
              datos_un_adquiriente=map_adquiriente_un(data.datos_adquirientes[0])
         )

    # 5. Inmuebles
    desc_inmuebles = []
    for i in data.desc_inmuebles:
        desc_inmuebles.append(DescInmueble(
            tipo_inmueble=i.tipo_inmueble,
            calle=i.calle,
            no_exterior=i.no_exterior,
            no_interior=i.no_interior,
            colonia=i.colonia,
            localidad=i.localidad,
            referencia=i.referencia,
            municipio=i.municipio,
            estado=i.estado,
            pais=i.pais,
            codigo_postal=i.codigo_postal
        ))

    # Construct NotariosPublicos complement
    return NotariosPublicos(
        desc_inmuebles=desc_inmuebles,
        datos_operacion=datos_operacion,
        datos_notario=datos_notario,
        datos_enajenante=datos_enajenante_obj,
        datos_adquiriente=datos_adquiriente_obj
    )

from decimal import Decimal
from typing import Tuple, List, Optional
from datetime import datetime

try:
    from satcfdi.create.cfd.notariospublicos10 import (
        NotariosPublicos,
        DescInmueble,
        DatosOperacion,
        DatosNotario,
        DatosAdquiriente,
        DatosEnajenante,
        DatosUnAdquiriente,
        DatosUnEnajenante,
        DatosAdquirienteCopSC,
        DatosEnajenanteCopSC
    )
except ImportError:
    pass

from .api_models import ComplementoNotariosModel, DatosAdquiriente as ApiDatosAdquiriente, DatosEnajenante as ApiDatosEnajenante

def split_name(full_name: str) -> Tuple[str, str]:
    """
    Splits a full name into ApellidoPaterno, ApellidoMaterno.
    Returns ('', '') when a single word input is provided.
    """
    parts = full_name.strip().split()
    if len(parts) <= 1:
        return ('', '')
    if len(parts) == 2:
        return (parts[1], '')
    if len(parts) >= 3:
        ap_materno = parts[-1]
        ap_paterno = parts[-2]
        return (ap_paterno, ap_materno)
    return ('', '')

def create_complemento_notarios(comp_data: ComplementoNotariosModel) -> 'NotariosPublicos':
    """
    Constructs the Complemento de Notarios Publicos from Pydantic model.
    """
    # 1. Validate Date
    fecha_inst_notarial_dt = datetime.fromisoformat(comp_data.datos_operacion.fecha_inst_notarial)
    if fecha_inst_notarial_dt > datetime.now():
        raise ValueError("FechaInstNotarial cannot be in the future")

    # 2. Build DatosNotario
    # Use default CURP if not provided or provided partially
    curp = 'TOSR520601HOCMXA00'
    num_notaria = 4
    entidad = '06'
    adscripcion = 'MANZANILLO COLIMA'

    if comp_data.datos_notario:
        if comp_data.datos_notario.curp:
             curp = comp_data.datos_notario.curp
        num_notaria = comp_data.datos_notario.num_notaria
        entidad = comp_data.datos_notario.entidad_federativa
        adscripcion = comp_data.datos_notario.adscripcion

    notario = DatosNotario(
        curp=curp,
        num_notaria=num_notaria,
        entidad_federativa=entidad,
        adscripcion=adscripcion
    )

    # 3. Build DatosOperacion
    operacion = DatosOperacion(
        num_instrumento_notarial=comp_data.datos_operacion.num_instrumento_notarial,
        fecha_inst_notarial=comp_data.datos_operacion.fecha_inst_notarial,
        monto_operacion=comp_data.datos_operacion.monto_operacion,
        subtotal=comp_data.datos_operacion.subtotal,
        iva=comp_data.datos_operacion.iva
    )

    # 4. Build DescInmuebles (note that we pass individual elements as arguments since it is a list of objects usually?
    # Wait, the prompt says "The satcfdi.create.cfd.notariospublicos10 module does not expose pluralized class names like DescInmuebles... it uses DescInmueble"
    # The NotariosPublicos constructor takes a list of DescInmueble as `desc_inmuebles`.
    inmuebles = [
        DescInmueble(
            tipo_inmueble=i.tipo_inmueble,
            calle=i.calle,
            municipio=i.municipio,
            estado=i.estado,
            pais=i.pais,
            codigo_postal=i.codigo_postal,
            no_exterior=i.no_exterior,
            no_interior=i.no_interior,
            colonia=i.colonia,
            localidad=i.localidad,
            referencia=i.referencia
        ) for i in comp_data.desc_inmuebles
    ]

    # Helper function to construct acquirers and alienators
    def build_participants(participants: list, is_adquiriente: bool):
        if not participants:
            raise ValueError("Participants list cannot be empty")

        is_copro = len(participants) > 1

        if is_copro:
            total_percent = sum([p.porcentaje for p in participants if p.porcentaje is not None])
            if total_percent != Decimal('100.00'):
                raise ValueError(f"Coproperty percentages must sum exactly to 100.00%, got {total_percent}")

        copro_e = 'Si' if is_copro else 'No'

        if is_adquiriente:
            if copro_e == 'No':
                p = participants[0]
                ap, am = split_name(p.nombre)
                n = p.nombre if (p.apellido_paterno or p.apellido_materno or not ap) else " ".join(p.nombre.strip().split()[:-2] if len(p.nombre.strip().split()) >= 3 else [p.nombre.strip().split()[0]])

                ap = p.apellido_paterno if p.apellido_paterno is not None else ap
                am = p.apellido_materno if p.apellido_materno is not None else am

                # Check for length == 2 case for nombre
                if p.apellido_paterno is None and p.apellido_materno is None and len(p.nombre.strip().split()) == 2:
                    n = p.nombre.strip().split()[0]

                un_adquiriente = DatosUnAdquiriente(
                    nombre=n,
                    apellido_paterno=ap,
                    apellido_materno=am,
                    rfc=p.rfc,
                    curp=p.curp
                )
                return DatosAdquiriente(
                    copro_soc_conyugal_e=copro_e,
                    datos_un_adquiriente=un_adquiriente
                )
            else:
                adquirientes_cop = []
                for p in participants:
                    ap, am = split_name(p.nombre)
                    n = p.nombre if (p.apellido_paterno or p.apellido_materno or not ap) else " ".join(p.nombre.strip().split()[:-2] if len(p.nombre.strip().split()) >= 3 else [p.nombre.strip().split()[0]])

                    ap = p.apellido_paterno if p.apellido_paterno is not None else ap
                    am = p.apellido_materno if p.apellido_materno is not None else am

                    if p.apellido_paterno is None and p.apellido_materno is None and len(p.nombre.strip().split()) == 2:
                        n = p.nombre.strip().split()[0]

                    adquirientes_cop.append(DatosAdquirienteCopSC(
                        nombre=n,
                        apellido_paterno=ap,
                        apellido_materno=am,
                        rfc=p.rfc,
                        curp=p.curp,
                        porcentaje=p.porcentaje
                    ))
                return DatosAdquiriente(
                    copro_soc_conyugal_e=copro_e,
                    datos_adquirientes_cop_sc=adquirientes_cop
                )
        else:
            if copro_e == 'No':
                p = participants[0]
                ap, am = split_name(p.nombre)
                n = p.nombre if (p.apellido_paterno or p.apellido_materno or not ap) else " ".join(p.nombre.strip().split()[:-2] if len(p.nombre.strip().split()) >= 3 else [p.nombre.strip().split()[0]])

                ap = p.apellido_paterno if p.apellido_paterno is not None else ap
                am = p.apellido_materno if p.apellido_materno is not None else am

                if p.apellido_paterno is None and p.apellido_materno is None and len(p.nombre.strip().split()) == 2:
                    n = p.nombre.strip().split()[0]

                un_enajenante = DatosUnEnajenante(
                    nombre=n,
                    apellido_paterno=ap,
                    apellido_materno=am,
                    rfc=p.rfc,
                    curp=p.curp
                )
                return DatosEnajenante(
                    copro_soc_conyugal_e=copro_e,
                    datos_un_enajenante=un_enajenante
                )
            else:
                enajenantes_cop = []
                for p in participants:
                    ap, am = split_name(p.nombre)
                    n = p.nombre if (p.apellido_paterno or p.apellido_materno or not ap) else " ".join(p.nombre.strip().split()[:-2] if len(p.nombre.strip().split()) >= 3 else [p.nombre.strip().split()[0]])

                    ap = p.apellido_paterno if p.apellido_paterno is not None else ap
                    am = p.apellido_materno if p.apellido_materno is not None else am

                    if p.apellido_paterno is None and p.apellido_materno is None and len(p.nombre.strip().split()) == 2:
                        n = p.nombre.strip().split()[0]

                    enajenantes_cop.append(DatosEnajenanteCopSC(
                        nombre=n,
                        apellido_paterno=ap,
                        apellido_materno=am,
                        rfc=p.rfc,
                        curp=p.curp,
                        porcentaje=p.porcentaje
                    ))
                return DatosEnajenante(
                    copro_soc_conyugal_e=copro_e,
                    datos_enajenantes_cop_sc=enajenantes_cop
                )

    adquiriente_node = build_participants(comp_data.datos_adquiriente, is_adquiriente=True)
    enajenante_node = build_participants(comp_data.datos_enajenante, is_adquiriente=False)

    return NotariosPublicos(
        desc_inmuebles=inmuebles,
        datos_operacion=operacion,
        datos_notario=notario,
        datos_adquiriente=adquiriente_node,
        datos_enajenante=enajenante_node
    )

"""
Business logic for AcuerdoTruequeMultiple entity.
Anemic Domain Model: Logic separated from data.
"""
from typing import TYPE_CHECKING, Optional, Union
from django.utils import timezone

if TYPE_CHECKING:
    from ..dominio.entidades import AcuerdoTruequeMultipleDominio


def esta_expirado(trueque_multiple: Union['AcuerdoTruequeMultipleDominio', object]) -> bool:
    """Verifica si el trueque múltiple ha expirado."""
    expira_el = getattr(trueque_multiple, 'expira_el', None)
    if expira_el is None:
        return False
    return timezone.now() > expira_el


def todos_aceptaron(trueque_multiple: Union['AcuerdoTruequeMultipleDominio', object]) -> bool:
    """Comprobar aceptación por emisores únicos del ciclo."""
    emisor1_id = getattr(trueque_multiple, 'emisor1_id', None)
    emisor2_id = getattr(trueque_multiple, 'emisor2_id', None)
    emisor3_id = getattr(trueque_multiple, 'emisor3_id', None)
    usuario1_aceptado = getattr(trueque_multiple, 'usuario1_aceptado', False)
    usuario2_aceptado = getattr(trueque_multiple, 'usuario2_aceptado', False)
    usuario3_aceptado = getattr(trueque_multiple, 'usuario3_aceptado', False)
    
    emisor_map = {
        1: emisor1_id,
        2: emisor2_id,
        3: emisor3_id,
    }

    unique_emis = set(emisor_map.values())
    for pid in unique_emis:
        if pid is None:
            return False
        acepto = False
        for idx, em_pid in emisor_map.items():
            if em_pid == pid:
                if idx == 1 and usuario1_aceptado:
                    acepto = True
                    break
                if idx == 2 and usuario2_aceptado:
                    acepto = True
                    break
                if idx == 3 and usuario3_aceptado:
                    acepto = True
                    break
        if not acepto:
            return False
    return True


def todos_pares_confirmaron(trueque_multiple: Union['AcuerdoTruequeMultipleDominio', object]) -> bool:
    par1_confirmado = getattr(trueque_multiple, 'par1_confirmado', False)
    par2_confirmado = getattr(trueque_multiple, 'par2_confirmado', False)
    par3_confirmado = getattr(trueque_multiple, 'par3_confirmado', False)
    return par1_confirmado and par2_confirmado and par3_confirmado


def esta_finalizado(trueque_multiple: Union['AcuerdoTruequeMultipleDominio', object]) -> bool:
    estado = getattr(trueque_multiple, 'estado', None)
    return estado == 'FINALIZADO'


def es_participante(trueque_multiple: Union['AcuerdoTruequeMultipleDominio', object], usuario) -> bool:
    """Verifica si un usuario es parte del trueque múltiple."""
    uid = getattr(usuario, 'id', None)
    if uid is None:
        try:
            uid = int(usuario)
        except Exception:
            return False
    
    emisor1_id = getattr(trueque_multiple, 'emisor1_id', None)
    receptor1_id = getattr(trueque_multiple, 'receptor1_id', None)
    emisor2_id = getattr(trueque_multiple, 'emisor2_id', None)
    receptor2_id = getattr(trueque_multiple, 'receptor2_id', None)
    emisor3_id = getattr(trueque_multiple, 'emisor3_id', None)
    receptor3_id = getattr(trueque_multiple, 'receptor3_id', None)
    
    return uid in (
        emisor1_id, receptor1_id,
        emisor2_id, receptor2_id,
        emisor3_id, receptor3_id,
    )


def obtener_rol(trueque_multiple: Union['AcuerdoTruequeMultipleDominio', object], usuario) -> Optional[int]:
    """Retorna el número de par (1, 2 o 3) en el que participa el usuario."""
    uid = getattr(usuario, 'id', None)
    if uid is None:
        try:
            uid = int(usuario)
        except Exception:
            return None
    
    emisor1_id = getattr(trueque_multiple, 'emisor1_id', None)
    emisor2_id = getattr(trueque_multiple, 'emisor2_id', None)
    emisor3_id = getattr(trueque_multiple, 'emisor3_id', None)
    receptor1_id = getattr(trueque_multiple, 'receptor1_id', None)
    receptor2_id = getattr(trueque_multiple, 'receptor2_id', None)
    receptor3_id = getattr(trueque_multiple, 'receptor3_id', None)
    
    # Preferir la correspondencia por emisor (cada emisor representa un
    # participante único del ciclo). Si no coincide, usar receptor como
    # fallback por compatibilidad.
    if uid == emisor1_id:
        return 1
    if uid == emisor2_id:
        return 2
    if uid == emisor3_id:
        return 3
    if uid == receptor1_id:
        return 1
    if uid == receptor2_id:
        return 2
    if uid == receptor3_id:
        return 3
    return None


def obtener_pares_del_usuario(trueque_multiple: Union['AcuerdoTruequeMultipleDominio', object], usuario) -> list:
    """Retorna una lista de pares (1, 2, o 3) en los que participa el usuario."""
    uid = getattr(usuario, 'id', None)
    if uid is None:
        try:
            uid = int(usuario)
        except Exception:
            return []
    
    emisor1_id = getattr(trueque_multiple, 'emisor1_id', None)
    receptor1_id = getattr(trueque_multiple, 'receptor1_id', None)
    emisor2_id = getattr(trueque_multiple, 'emisor2_id', None)
    receptor2_id = getattr(trueque_multiple, 'receptor2_id', None)
    emisor3_id = getattr(trueque_multiple, 'emisor3_id', None)
    receptor3_id = getattr(trueque_multiple, 'receptor3_id', None)
    
    pares = []
    
    # Verificar participación en cada par
    if uid in (emisor1_id, receptor1_id):
        pares.append(1)
    if uid in (emisor2_id, receptor2_id):
        pares.append(2)
    if uid in (emisor3_id, receptor3_id):
        pares.append(3)
    
    return pares

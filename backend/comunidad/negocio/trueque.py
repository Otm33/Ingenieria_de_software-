"""
Business logic for AcuerdoTrueque entity.
Anemic Domain Model: Logic separated from data.
"""
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from ..dominio.entidades import AcuerdoTruequeDominio


def esta_pendiente(trueque: Union['AcuerdoTruequeDominio', object]) -> bool:
    estado = getattr(trueque, 'estado', None)
    return estado == 'PENDIENTE'


def esta_aceptado(trueque: Union['AcuerdoTruequeDominio', object]) -> bool:
    estado = getattr(trueque, 'estado', None)
    return estado == 'ACEPTADO'


def esta_en_curso(trueque: Union['AcuerdoTruequeDominio', object]) -> bool:
    estado = getattr(trueque, 'estado', None)
    return estado == 'EN_CURSO'


def esta_finalizado(trueque: Union['AcuerdoTruequeDominio', object]) -> bool:
    estado = getattr(trueque, 'estado', None)
    return estado == 'FINALIZADO'


def ambas_partes_confirmaron(trueque: Union['AcuerdoTruequeDominio', object]) -> bool:
    """HU4: Ambas partes confirmaron la finalización."""
    emisor_confirmado = getattr(trueque, 'emisor_confirmado', False)
    receptor_confirmado = getattr(trueque, 'receptor_confirmado', False)
    return emisor_confirmado and receptor_confirmado


def puede_confirmar(trueque: Union['AcuerdoTruequeDominio', object], usuario) -> tuple[bool, str]:
    """HU4: Verifica si un usuario puede confirmar la finalización."""
    estado = getattr(trueque, 'estado', None)
    
    # Aceptar confirmaciones cuando el trueque está ACEPTADO o EN_CURSO
    if estado not in ('ACEPTADO', 'EN_CURSO'):
        return False, "Solo se pueden confirmar trueques en curso."
    
    # Obtener ID del usuario
    uid = getattr(usuario, 'id', None)
    if uid is None:
        try:
            uid = int(usuario)
        except Exception:
            return False, "Usuario inválido"
    
    emisor_id = getattr(trueque, 'emisor_id', None)
    receptor_id = getattr(trueque, 'receptor_id', None)
    
    if uid in (emisor_id, receptor_id):
        return True, "Puede confirmar"
    return False, "Usuario no es parte del trueque."


def es_participante(trueque: Union['AcuerdoTruequeDominio', object], usuario) -> bool:
    """Verifica si un usuario es parte del trueque."""
    uid = getattr(usuario, 'id', None)
    if uid is None:
        try:
            uid = int(usuario)
        except Exception:
            return False
    
    emisor_id = getattr(trueque, 'emisor_id', None)
    receptor_id = getattr(trueque, 'receptor_id', None)
    
    return uid in (emisor_id, receptor_id)


def contraparte_id(trueque: Union['AcuerdoTruequeDominio', object], usuario) -> Optional[int]:
    """Retorna el ID de la contraparte del usuario en el trueque.

    Returns:
        int — ID de la contraparte, o None si el usuario no es participante.
    """
    uid = getattr(usuario, 'id', None)
    if uid is None:
        try:
            uid = int(usuario)
        except Exception:
            return None

    emisor_id = getattr(trueque, 'emisor_id', None)
    receptor_id = getattr(trueque, 'receptor_id', None)

    if uid == emisor_id:
        return receptor_id
    if uid == receptor_id:
        return emisor_id
    return None


# Alias de retrocompatibilidad — TODO: migrar callers a contraparte_id
contraparte = contraparte_id


def es_intercambio_mutuo(tipo_pub_emisor: Optional[str], tipo_pub_receptor: Optional[str]) -> bool:
    """Trueque complementario: ambas partes ofrecen un TALENTO (impacto 0 horas).

    Función PURA de negocio — no accede a BD ni a ORM.
    El caller (servicio) es responsable de resolver los tipos antes de invocar.
    """
    if not tipo_pub_emisor or not tipo_pub_receptor:
        return False
    return tipo_pub_emisor == 'TALENTO' and tipo_pub_receptor == 'TALENTO'

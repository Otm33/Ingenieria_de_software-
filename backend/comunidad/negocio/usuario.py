"""
Business logic for Usuario entity.
Anemic Domain Model: Logic separated from data.
"""
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ..dominio.entidades import UsuarioDominio


def tiene_saldo_critico(usuario: Union['UsuarioDominio', object]) -> bool:
    """HU2: Saldo inferior a -10 horas bloquea publicar y modificar."""
    # Soporte tanto para UsuarioDominio como para ORM (compatibilidad temporal)
    horas = getattr(usuario, 'horas_de_vida', None)
    if horas is None:
        return False
    return horas < -10.0


def puede_modificar_publicaciones(usuario: Union['UsuarioDominio', object]) -> bool:
    return not tiene_saldo_critico(usuario)


def es_comercio_activo(usuario: Union['UsuarioDominio', object]) -> bool:
    """HU5: Solo comercios activos pueden emitir vuelto."""
    es_comercio = getattr(usuario, 'es_comercio', False)
    is_active = getattr(usuario, 'is_active', True)
    return es_comercio and is_active


def puede_publicar(usuario: Union['UsuarioDominio', object], tipo_publicacion: str, conteo_actual: int) -> tuple[bool, str]:
    if tiene_saldo_critico(usuario):
        return False, "Saldo crítico inferior a -10 horas. No puedes publicar."

    if tipo_publicacion == 'TALENTO' and conteo_actual >= 5:
        return False, "No puedes tener más de 5 talentos activos publicados simultáneamente."

    if tipo_publicacion == 'NECESIDAD' and conteo_actual >= 3:
        return False, "No puedes tener más de 3 necesidades activas simultáneamente."

    return True, "Puede publicar"


def puede_emitir_vuelto_comercial(usuario: Union['UsuarioDominio', object], monto: float) -> tuple[bool, str]:
    if not es_comercio_activo(usuario):
        return False, "Solo los comercios activos pueden emitir vuelto."
    saldo_comercial = getattr(usuario, 'saldo_comercial', 0)
    if saldo_comercial < monto:
        return False, "Saldo comercial insuficiente para emitir vuelto."
    return True, "Puede emitir vuelto"


def puede_pagar_con_saldo(usuario: Union['UsuarioDominio', object], monto: float) -> tuple[bool, str]:
    if getattr(usuario, 'es_comercio', False):
        return False, "Los comercios no pueden pagar con saldo comercial."
    saldo_comercial = getattr(usuario, 'saldo_comercial', 0)
    if saldo_comercial < monto:
        return False, "Saldo comercial insuficiente."
    return True, "Puede pagar con saldo"


def es_miembro_activo(usuario: Union['UsuarioDominio', object], tiene_publicaciones: bool) -> bool:
    """HU2: Miembro activo si tiene nombre real y al menos una publicación."""
    nombre_real = getattr(usuario, 'nombre_real', "")
    nombre = (nombre_real or "").strip()
    return bool(nombre and tiene_publicaciones)

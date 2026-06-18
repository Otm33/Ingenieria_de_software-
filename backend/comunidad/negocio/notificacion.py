"""
Business logic for Notificacion entity.
Anemic Domain Model: Logic separated from data.
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..dominio.entidades import NotificacionDominio


def esta_leida(notificacion: 'NotificacionDominio') -> bool:
    return notificacion.estado == 'LEIDA'


def es_de_tipo_match(notificacion: 'NotificacionDominio') -> bool:
    return notificacion.tipo == 'MATCH'


def es_de_tipo_propuesta(notificacion: 'NotificacionDominio') -> bool:
    return notificacion.tipo == 'PROPUESTA'

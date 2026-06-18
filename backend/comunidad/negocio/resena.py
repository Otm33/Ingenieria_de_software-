"""
Business logic for Resena entity.
Anemic Domain Model: Logic separated from data.
"""
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ..dominio.entidades import ResenaDominio


def calificacion_valida(resena: Union['ResenaDominio', object]) -> bool:
    estrellas = getattr(resena, 'estrellas', None)
    if estrellas is None:
        return False
    return 1 <= int(estrellas) <= 5


def comentario_valido(resena: Union['ResenaDominio', object]) -> tuple[bool, str]:
    comentario = getattr(resena, 'comentario', None)
    if not comentario or not str(comentario).strip():
        return False, "El comentario no puede estar vacío."
    if len(str(comentario)) > 500:
        return False, "El comentario no puede exceder 500 caracteres."
    return True, "Comentario válido"


def validar(resena: Union['ResenaDominio', object]) -> tuple[bool, str]:
    if not calificacion_valida(resena):
        return False, "La calificación debe estar entre 1 y 5 estrellas."
    valido, mensaje = comentario_valido(resena)
    if not valido:
        return False, mensaje
    return True, "Reseña válida"


def es_positiva(resena: Union['ResenaDominio', object]) -> bool:
    estrellas = getattr(resena, 'estrellas', None)
    return estrellas is not None and estrellas >= 4


def es_negativa(resena: Union['ResenaDominio', object]) -> bool:
    estrellas = getattr(resena, 'estrellas', None)
    return estrellas is not None and estrellas <= 2

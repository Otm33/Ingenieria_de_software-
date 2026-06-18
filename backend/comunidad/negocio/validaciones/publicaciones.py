"""
Validaciones de contenido para Publicaciones.

Contiene la lista negra de palabras prohibidas y la función que verifica
si un texto (título o descripción de una publicación) contiene alguna de ellas.

Regla de negocio:
    No se pueden crear publicaciones cuyo título o descripción incluyan
    términos de contenido inapropiado. La verificación es case-insensitive.

Llamado desde:
    ``services/publicacion.py`` → ``PublicacionService.crear()``
"""
from __future__ import annotations

from typing import List


PALABRAS_PROHIBIDAS: List[str] = [
    "sexo",
    "pornografia",
    "drogas",
    "droga",
    "arma",
    "estafa",
    "fraude",
    "hack",
    "terrorismo",
    "trata",
]


def contiene_palabra_prohibida(texto: str) -> bool:
    """Retorna True si `texto` contiene alguna palabra prohibida (case-insensitive)."""
    if not texto:
        return False

    texto_lower = texto.lower()
    return any(palabra.lower() in texto_lower for palabra in PALABRAS_PROHIBIDAS)

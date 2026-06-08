from __future__ import annotations

from typing import List


# Lista de palabras prohibidas para el contenido de publicaciones.
# Se mantiene en ASCII para evitar problemas de codificacion/acentos.
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
    """
    Retorna True si `texto` contiene alguna palabra prohibida (case-insensitive).
    """
    if not texto:
        return False

    texto_lower = texto.lower()
    return any(palabra.lower() in texto_lower for palabra in PALABRAS_PROHIBIDAS)


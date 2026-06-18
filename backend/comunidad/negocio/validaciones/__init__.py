"""
Capa de Negocio — Submódulo de Validaciones de contenido.

Este paquete contiene reglas de validación de contenido que se aplican a
las publicaciones y otros textos del sistema (títulos, descripciones).

Responsabilidad:
    - Filtrado de palabras prohibidas (contenido inapropiado).
    - Validaciones que dependen de reglas de contenido, no de reglas de negocio
      puras (esas viven en ``negocio/*.py``).

Uso:
    Los Servicios (ej: ``PublicacionService.crear()``) importan estas funciones
    para validar el contenido antes de persistirlo.
"""
from .publicaciones import PALABRAS_PROHIBIDAS, contiene_palabra_prohibida

__all__ = ["PALABRAS_PROHIBIDAS", "contiene_palabra_prohibida"]

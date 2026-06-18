"""
Sprint 2 HU1: Whitelist curada de causas sociales permitidas.
Solo necesidades de personas vulnerables (cuidado, salud, educación inclusiva, movilidad).
Mantener sincronizado con frontend/src/data/catalogoCausasSociales.js
"""

# Títulos permitidos como causa social, agrupados por categoría
TITULOS_CAUSA_SOCIAL = {
    "Cuidado de la Salud, Bienestar y Terapias": [
        "Cuidado de abuelos",
        "Acompañamiento médico",
        "Cuidado de pacientes",
        "Enfermería a domicilio",
        "Inyectología",
        "Curación de heridas",
        "Control de tensión",
        "Fisioterapia en casa",
        "Rehabilitación física",
        "Terapia ocupacional",
        "Terapia de lenguaje",
        "Estimulación temprana",
        "Gimnasia prenatal",
        "Terapia de duelo",
        "Orientación familiar",
        "Psicoterapia clínica",
    ],
    "Educación, Asesoría y Tutorías": [
        "Apoyo escolar primaria",
        "Apoyo bachillerato",
        "Redacción en español",
        "Técnicas de estudio",
    ],
    "Automotriz, Transporte y Logística": [
        "Conductor de reemplazo",
        "Chófer privado",
        "Transporte escolar",
    ],
}

# Set plano de todos los títulos permitidos (para O(1) lookup)
_TITULOS_PERMITIDOS = {
    titulo
    for titulos in TITULOS_CAUSA_SOCIAL.values()
    for titulo in titulos
}

CATEGORIAS_CAUSA_SOCIAL = list(TITULOS_CAUSA_SOCIAL.keys())

TITULOS_CAUSA_SOCIAL_PERMITIDOS = list(_TITULOS_PERMITIDOS)


def es_titulo_causa_social_permitido(titulo: str) -> bool:
    """Verifica si un título está en la whitelist de causas sociales."""
    return titulo in _TITULOS_PERMITIDOS


def es_categoria_causa_social_permitida(categoria: str) -> bool:
    """Verifica si una categoría tiene causas sociales permitidas."""
    return categoria in TITULOS_CAUSA_SOCIAL


def categoria_para_titulo(titulo: str) -> str | None:
    """Retorna la categoría a la que pertenece un título de causa social."""
    for categoria, titulos in TITULOS_CAUSA_SOCIAL.items():
        if titulo in titulos:
            return categoria
    return None

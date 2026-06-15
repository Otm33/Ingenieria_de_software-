"""
Whitelist curada de causas sociales: subset del catálogo de cartelera.
Solo necesidades de personas vulnerables (cuidado, salud, educación inclusiva, movilidad).
Mantener sincronizado con frontend/src/data/catalogoCausasSociales.js
"""

from .catalogo_servicios import TITULOS_POR_CATEGORIA

TITULOS_CAUSA_SOCIAL_PERMITIDOS = [
    # Cuidado de la Salud, Bienestar y Terapias
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
    # Educación, Asesoría y Tutorías
    "Apoyo escolar primaria",
    "Apoyo bachillerato",
    "Redacción en español",
    "Técnicas de estudio",
    # Automotriz, Transporte y Logística
    "Conductor de reemplazo",
    "Chófer privado",
    "Transporte escolar",
]

_PERMITIDOS = set(TITULOS_CAUSA_SOCIAL_PERMITIDOS)

TITULOS_CAUSA_SOCIAL = {
    categoria: [
        titulo
        for titulo in titulos
        if titulo in _PERMITIDOS
    ]
    for categoria, titulos in TITULOS_POR_CATEGORIA.items()
    if any(titulo in _PERMITIDOS for titulo in titulos)
}

CATEGORIAS_CAUSA_SOCIAL = list(TITULOS_CAUSA_SOCIAL.keys())

MAPEO_TITULOS_CATALOGO_ANTIGUO = {
    "Acompañamiento a adulto mayor": (
        "Cuidado de abuelos",
        "Cuidado de la Salud, Bienestar y Terapias",
    ),
}


def es_titulo_causa_social_permitido(titulo):
    return titulo in _PERMITIDOS


def es_categoria_causa_social_permitida(categoria):
    return categoria in CATEGORIAS_CAUSA_SOCIAL


def categoria_para_titulo(titulo):
    for categoria, titulos in TITULOS_CAUSA_SOCIAL.items():
        if titulo in titulos:
            return categoria
    return None


def titulo_pertenece_a_catalogo_cartelera(categoria, titulo):
    return titulo in TITULOS_POR_CATEGORIA.get(categoria, ())

"""
Business logic for Publicacion entity.
Anemic Domain Model: Logic separated from data.
"""
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ..dominio.entidades import UsuarioDominio, PublicacionDominio
    from .usuario import puede_modificar_publicaciones, puede_publicar


def es_talento(publicacion: Union['PublicacionDominio', object]) -> bool:
    tipo = getattr(publicacion, 'tipo', None)
    return tipo == 'TALENTO'


def es_necesidad(publicacion: Union['PublicacionDominio', object]) -> bool:
    tipo = getattr(publicacion, 'tipo', None)
    return tipo == 'NECESIDAD'


def es_urgente(publicacion: Union['PublicacionDominio', object]) -> bool:
    """HU3: Urgencia Alta o Crítica."""
    urgencia = getattr(publicacion, 'urgencia', None)
    return urgencia in ['ALTA', 'CRITICA']


def es_critica(publicacion: Union['PublicacionDominio', object]) -> bool:
    urgencia = getattr(publicacion, 'urgencia', None)
    return urgencia == 'CRITICA'


def validar_reglas_negocio(
    usuario,
    tipo: str,
    titulo: str,
    descripcion: str,
    categoria: str,
    urgencia: str,
    esta_activa: bool,
    conteo_actual: int,
    es_nueva: bool = True,
    titulo_existente: bool = False,
) -> tuple[bool, str]:
    from .usuario import puede_modificar_publicaciones, puede_publicar

    # Check if user can modify publications
    if not puede_modificar_publicaciones(usuario):
        return False, "Saldo crítico inferior a -10 horas. Operación bloqueada."

    # Talentos can only have NORMAL urgency
    if tipo == "TALENTO" and urgencia != "NORMAL":
        return False, "Los talentos solo pueden tener urgencia Normal."

    # Verificar que el usuario no tenga una publicación con el mismo título
    if es_nueva and titulo_existente:
        return False, "Ya tienes una publicación con este título. Por favor usa un título diferente."

    # Check if user can publish new publications
    if es_nueva and esta_activa:
        puede, msj = puede_publicar(usuario, tipo, conteo_actual)
        if not puede:
            return False, msj

    return True, "Validación exitosa"


def puede_pausarse(publicacion: Union['PublicacionDominio', object]) -> tuple[bool, str]:
    return True, "Puede pausar"


def puede_reactivarse(
    publicacion: Union['PublicacionDominio', object],
    usuario,
    conteo_actual: int,
) -> tuple[bool, str]:
    """Reutilizar validar_reglas_negocio para comprobar límites al reactivar."""
    tipo = getattr(publicacion, 'tipo', None)
    titulo = getattr(publicacion, 'titulo', None)
    descripcion = getattr(publicacion, 'descripcion', None)
    categoria = getattr(publicacion, 'categoria', None)
    urgencia = getattr(publicacion, 'urgencia', None)
    esta_activa = True
    
    return validar_reglas_negocio(
        usuario=usuario,
        tipo=tipo,
        titulo=titulo,
        descripcion=descripcion,
        categoria=categoria,
        urgencia=urgencia,
        esta_activa=esta_activa,
        conteo_actual=conteo_actual,
        es_nueva=False,
    )

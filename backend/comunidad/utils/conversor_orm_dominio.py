"""
Módulo de conversión ORM→Dominio.
Contiene funciones para convertir objetos ORM de Django a entidades de dominio.

NOTA: Las conversiones de Publicacion, AcuerdoTrueque y Resena las realizan
los métodos _modelo_a_dominio() internos de cada repositorio. Este módulo solo
mantiene la conversión de Usuario, que es usada en el flujo de autenticación
(router → controlador).
"""

from ..models import Usuario
from ..dominio.entidades import UsuarioDominio


def usuario_orm_a_dominio(usuario_orm: Usuario) -> UsuarioDominio:
    """Convierte un objeto ORM Usuario a una entidad de dominio UsuarioDominio."""
    return UsuarioDominio(
        id=usuario_orm.id,
        username=usuario_orm.username,
        email=usuario_orm.email,
        nombre_real=usuario_orm.nombre_real,
        horas_de_vida=float(usuario_orm.horas_de_vida),
        es_comercio=usuario_orm.es_comercio,
        saldo_comercial=float(usuario_orm.saldo_comercial),
        is_active=usuario_orm.is_active,
        is_staff=usuario_orm.is_staff,
        is_superuser=usuario_orm.is_superuser,
        promedio_estrellas=float(usuario_orm.promedio_estrellas or 0.0),
        # Sprint 2 HU1: Impacto Social
        estado_social=getattr(usuario_orm, 'estado_social', 'NINGUNO'),
        horas_recibidas_donacion=float(getattr(usuario_orm, 'horas_recibidas_donacion', 0.0)),
        es_fondo_comunitario=getattr(usuario_orm, 'es_fondo_comunitario', False),
    )

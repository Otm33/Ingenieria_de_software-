"""
Capa de Dominio — Entidades puras del negocio (Anemic Domain Model).

Arquitectura N-Tier / Clean Architecture:
    Estas dataclasses representan los objetos del mundo real (usuario, publicación,
    trueque, reseña, notificación) SIN ningún conocimiento de tecnología, ORM ni
    frameworks.  Son la "verdad" del sistema.

Regla de pureza:
    - Solo importan ``dataclasses``, ``datetime`` y ``typing``.
    - NO importan Django, SQLAlchemy ni cualquier otra dependencia tecnológica.
    - NO contienen lógica de negocio (eso vive en ``negocio/``).
    - NO contienen métodos de persistencia (.save(), .delete(), etc.).

Flujo de uso:
    Los Repositorios (capa de Persistencia) convierten ORM → Entidad de Dominio
    mediante ``_modelo_a_dominio()`` y las pasan a los Servicios y Controladores.
    Así las capas superiores nunca tocan objetos ORM de Django.

Campos desnormalizados:
    Campos como ``usuario_nombre_real`` o ``usuario_promedio_estrellas`` en
    ``PublicacionDominio`` son poblados por el repositorio al momento de la
    conversión, para evitar que las capas superiores hagan queries adicionales.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List



@dataclass
class UsuarioDominio:
    """HU2: Perfil del usuario con balance de Horas de Vida y reputación."""
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    nombre_real: str = ""
    horas_de_vida: float = 0.0
    es_comercio: bool = False
    saldo_comercial: float = 0.0
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False
    promedio_estrellas: float = 0.0
    # Sprint 2 HU1: Impacto Social
    estado_social: str = 'NINGUNO'
    horas_recibidas_donacion: float = 0.0
    es_fondo_comunitario: bool = False


@dataclass
class UsuarioAutorizadoDominio:
    """Representación en dominio de correos autorizados en lista blanca."""
    id: Optional[int] = None
    email: str = ""
    tipo: str = "USUARIO"


@dataclass
class PublicacionDominio:
    """HU2/HU3: Catálogo de talentos y necesidades.

    Los campos usuario_nombre_real y usuario_promedio_estrellas son datos
    desnormalizados que el Repositorio puebla al mapear ORM → Dominio.
    La entidad de dominio NO accede al ORM directamente.
    """
    id: Optional[int] = None
    usuario_id: int = 0
    tipo: str = "TALENTO"
    titulo: str = ""
    descripcion: str = ""
    categoria: str = ""
    urgencia: str = "NORMAL"
    esta_activa: bool = True
    es_causa_social: bool = False
    fecha_creacion: Optional[datetime] = None
    # Datos del autor: poblados por el repositorio, nunca consultados con ORM aquí
    usuario_nombre_real: str = ""
    usuario_promedio_estrellas: float = 0.0
    usuario_username: str = ""
    usuario_is_active: bool = True
    usuario_horas_de_vida: float = 0.0


@dataclass
class AcuerdoTruequeDominio:
    """HU4: Propuesta de trueque entre dos usuarios."""
    id: Optional[int] = None
    emisor_id: int = 0
    receptor_id: int = 0
    estado: str = "PENDIENTE"
    publicacion_emisor_id: Optional[int] = None
    publicacion_receptor_id: Optional[int] = None
    emisor_confirmado: bool = False
    receptor_confirmado: bool = False
    codigo_confirmacion: Optional[str] = None


@dataclass
class ResenaDominio:
    """HU4: Calificación post-trueque."""
    id: Optional[int] = None
    trueque_id: int = 0
    calificador_id: int = 0
    calificado_id: int = 0
    estrellas: int = 5
    comentario: str = ""


@dataclass
class NotificacionDominio:
    """Notificación de propuesta o match."""
    id: Optional[int] = None
    tipo: str = "PROPUESTA"
    destinatario_id: int = 0
    remitente_id: int = 0
    trueque_id: Optional[int] = None
    trueque_multiple_id: Optional[int] = None
    publicacion_original_id: Optional[int] = None
    mensaje: str = ""
    estado: str = "PENDIENTE"
    match_detalle: Optional[list] = None


@dataclass
class AcuerdoTruequeMultipleDominio:
    """HU Trueque Múltiple: ciclo A→B→C→A entre 3 usuarios."""
    id: Optional[int] = None
    estado: str = "PENDIENTE"
    emisor1_id: int = 0
    receptor1_id: int = 0
    emisor2_id: int = 0
    receptor2_id: int = 0
    emisor3_id: int = 0
    receptor3_id: int = 0
    usuario1_aceptado: bool = False
    usuario2_aceptado: bool = False
    usuario3_aceptado: bool = False
    par1_confirmado: bool = False
    par2_confirmado: bool = False
    par3_confirmado: bool = False
    codigo_par1: Optional[str] = None
    codigo_par2: Optional[str] = None
    codigo_par3: Optional[str] = None
    fecha_creacion: Optional[datetime] = None


@dataclass
class ResenaMultipleDominio:
    """HU Trueque Múltiple: Calificación post-trueque múltiple."""
    id: Optional[int] = None
    trueque_multiple_id: int = 0
    calificador_id: int = 0
    calificado_id: int = 0
    estrellas: int = 5
    comentario: str = ""


# ── Sprint 2 HU1: Impacto Social ─────────────────────────────────────────────

@dataclass
class SolicitudApoyoSocialDominio:
    """Sprint 2 HU1: Solicitud de apoyo social (entidad de dominio pura)."""
    id: Optional[int] = None
    solicitante_id: int = 0
    categoria: str = ""
    titulo: str = ""
    descripcion: str = ""
    estado: str = "PENDIENTE"
    horas_recibidas: float = 0.0
    horas_solidarias_disponibles: float = 0.0
    horas_solidarias_utilizadas: float = 0.0
    publicacion_id: Optional[int] = None
    aprobada_por_id: Optional[int] = None
    creado_el: Optional[datetime] = None
    actualizado_el: Optional[datetime] = None
    # Datos desnormalizados para presentación (poblados por repositorio)
    solicitante_nombre: str = ""
    estado_social_solicitante: str = "NINGUNO"
    necesidad_activa: bool = False


@dataclass
class DonacionHorasDominio:
    """Sprint 2 HU1: Registro de donación de Horas de Vida (ledger inmutable)."""
    id: Optional[int] = None
    donante_id: int = 0
    receptor_id: int = 0
    solicitud_id: Optional[int] = None
    monto: float = 0.0
    tipo_destino: str = "CAUSA"
    fecha: Optional[datetime] = None
    comprobante_id: Optional[str] = None
    # Datos desnormalizados para presentación
    donante_nombre: str = ""
    receptor_nombre: str = ""

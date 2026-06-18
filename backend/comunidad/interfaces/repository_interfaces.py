"""
Capa de Interfaces — Contratos abstractos de Repositorios (DIP).

Arquitectura N-Tier / Clean Architecture:
    Estas clases abstractas (ABC) definen QUÉ operaciones de persistencia
    deben existir, pero NO cómo se implementan.  Esto permite:

    1. Que los Servicios dependan de la abstracción, no de Django ORM.
    2. Sustituir la implementación (ej: PostgreSQL → MongoDB) sin tocar lógica.
    3. Facilitar testing con mocks/stubs.

Principio de Inversión de Dependencias (DIP):
    La capa de Negocio/Servicios importa estas interfaces.
    La capa de Persistencia (``repositorios_implementacion.py``) las implementa.
    Nunca al revés.

Convención de nombres:
    - ``I`` + nombre del dominio + ``Repository``
    - Cada método abstracto refleja una operación CRUD o query específica.
    - Los tipos de retorno son siempre entidades de dominio (``*Dominio``),
      nunca objetos ORM.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from ..dominio.entidades import (
    AcuerdoTruequeDominio,
    NotificacionDominio,
    PublicacionDominio,
    ResenaDominio,
    UsuarioDominio,
)


class IUsuarioRepository(ABC):
    """Contrato para acceso a datos de usuarios."""

    @abstractmethod
    def obtener_por_id(self, usuario_id: int) -> Optional[UsuarioDominio]:
        pass

    @abstractmethod
    def obtener_por_email(self, email: str) -> Optional[UsuarioDominio]:
        pass

    @abstractmethod
    def obtener_por_username(self, username: str) -> Optional[UsuarioDominio]:
        pass

    @abstractmethod
    def guardar(self, usuario_dominio: UsuarioDominio, password: str = None) -> UsuarioDominio:
        pass

    @abstractmethod
    def listar_activos(self) -> List[UsuarioDominio]:
        pass

    @abstractmethod
    def listar_comercios_activos(self) -> List[UsuarioDominio]:
        pass

    # ── Admin Panel (Sprint 2 HU3) ──

    @abstractmethod
    def listar_todos(self, busqueda: Optional[str] = None) -> List[UsuarioDominio]:
        pass

    @abstractmethod
    def actualizar_estado(self, usuario_id: int, is_active: bool) -> UsuarioDominio:
        pass

    @abstractmethod
    def actualizar_rol(self, usuario_id: int, is_staff: bool) -> UsuarioDominio:
        pass

    @abstractmethod
    def eliminar(self, usuario_id: int) -> None:
        pass

    @abstractmethod
    def contar_estadisticas(self) -> dict:
        pass


class IPublicacionRepository(ABC):
    """Contrato para acceso a datos de publicaciones."""

    @abstractmethod
    def obtener_por_id(self, publicacion_id: int) -> Optional[PublicacionDominio]:
        pass

    @abstractmethod
    def guardar(self, publicacion_dominio: PublicacionDominio) -> PublicacionDominio:
        pass

    @abstractmethod
    def contar_activas_por_tipo(self, usuario_id: int, tipo: str) -> int:
        pass

    @abstractmethod
    def listar_por_usuario(self, usuario_id: int, solo_activas: bool = False) -> List[PublicacionDominio]:
        pass

    @abstractmethod
    def obtener_cartelera(self, categoria: Optional[str] = None, urgencias: Optional[List[str]] = None) -> List[PublicacionDominio]:
        pass

    # ── Admin Panel (Sprint 2 HU3) ──

    @abstractmethod
    def listar_todas(self, busqueda: Optional[str] = None) -> List[PublicacionDominio]:
        pass

    @abstractmethod
    def eliminar(self, publicacion_id: int) -> None:
        pass

    @abstractmethod
    def actualizar_estado_admin(self, publicacion_id: int, esta_activa: bool) -> PublicacionDominio:
        pass


class ITruequeRepository(ABC):
    """Contrato para acceso a datos de acuerdos de trueque."""

    @abstractmethod
    def obtener_por_id(self, trueque_id: int) -> Optional[AcuerdoTruequeDominio]:
        pass

    @abstractmethod
    def guardar(self, trueque_dominio: AcuerdoTruequeDominio) -> AcuerdoTruequeDominio:
        pass

    @abstractmethod
    def listar_por_usuario(self, usuario_id: int) -> List[AcuerdoTruequeDominio]:
        pass

    # ── Admin Panel (Sprint 2 HU3) ──

    @abstractmethod
    def listar_todos(self, busqueda: Optional[str] = None) -> List[AcuerdoTruequeDominio]:
        pass

    @abstractmethod
    def actualizar_estado_admin(self, trueque_id: int, estado: str) -> AcuerdoTruequeDominio:
        pass

    @abstractmethod
    def eliminar(self, trueque_id: int) -> None:
        pass


class IResenaRepository(ABC):
    """Contrato para acceso a datos de reseñas."""

    @abstractmethod
    def crear(self, trueque_id: int, calificador_id: int, calificado_id: int, estrellas: int, comentario: str) -> ResenaDominio:
        pass

    @abstractmethod
    def listar_por_calificado(self, usuario_id: int) -> List[ResenaDominio]:
        pass

    @abstractmethod
    def existe_resena(self, trueque_id: int, calificador_id: int) -> bool:
        pass

    # ── Admin Panel (Sprint 2 HU3) ──

    @abstractmethod
    def listar_todas(self, busqueda: Optional[str] = None) -> List[ResenaDominio]:
        pass

    @abstractmethod
    def eliminar(self, resena_id: int) -> None:
        pass


class INotificacionRepository(ABC):
    """Contrato para acceso a datos de notificaciones."""

    @abstractmethod
    def listar_por_destinatario(
        self,
        usuario_id: int,
        incluir_leidas: bool = False,
    ) -> List[NotificacionDominio]:
        pass

    @abstractmethod
    def marcar_como_leida(self, notificacion_id: int, usuario_id: int) -> NotificacionDominio:
        pass


class ITruequeMultipleRepository(ABC):
    """Contrato para acuerdos de trueque múltiple."""

    @abstractmethod
    def obtener_por_id(self, trueque_multiple_id: int):
        pass

    @abstractmethod
    def guardar(self, trueque_multiple_dominio):
        pass

    @abstractmethod
    def listar_por_usuario(self, usuario_id: int):
        pass

    # ── Admin Panel (Sprint 2 HU3) ──

    @abstractmethod
    def listar_todos(self, busqueda=None):
        pass

    @abstractmethod
    def actualizar_estado_admin(self, trueque_multiple_id: int, estado: str):
        pass

    @abstractmethod
    def eliminar(self, trueque_multiple_id: int):
        pass


class ISaldoComercialRepository(ABC):
    """Contrato para movimientos de saldo comercial."""

    @abstractmethod
    def crear_movimiento(self, comercio_id: int, cliente_id: int, monto: float, tipo_movimiento: str, valor_producto: float = None, monto_recibido: float = None):
        pass

    @abstractmethod
    def obtener_saldo(self, usuario_id: int) -> float:
        pass

    # ── Admin Panel (Sprint 2 HU3) ──

    @abstractmethod
    def listar_todos(self, busqueda=None):
        pass


class IResenaMultipleRepository(ABC):
    """Contrato para acceso a datos de resenas multiples."""

    @abstractmethod
    def crear(self, trueque_multiple_id: int, calificador_id: int, calificado_id: int, estrellas: int, comentario: str):
        pass

    @abstractmethod
    def existe_resena(self, trueque_multiple_id: int, calificador_id: int, calificado_id: int) -> bool:
        pass

    # ── Admin Panel (Sprint 2 HU3) ──

    @abstractmethod
    def listar_todas(self, busqueda=None):
        pass

    @abstractmethod
    def eliminar(self, resena_multiple_id: int):
        pass


# ── Sprint 2 HU1: Impacto Social ─────────────────────────────────────────────

class ISolicitudApoyoSocialRepository(ABC):
    """Contrato para acceso a datos de solicitudes de apoyo social."""

    @abstractmethod
    def crear(self, solicitante_id: int, categoria: str, titulo: str, descripcion: str):
        pass

    @abstractmethod
    def obtener_orm(self, solicitud_id: int):
        pass

    @abstractmethod
    def listar_aprobadas(self) -> list:
        pass

    @abstractmethod
    def listar_por_solicitante(self, usuario_id: int) -> list:
        pass

    @abstractmethod
    def listar_pendientes(self) -> list:
        pass

    @abstractmethod
    def vincular_publicacion(self, solicitud_id: int, publicacion_id: int):
        pass

    @abstractmethod
    def aprobar(self, solicitud_id: int, admin_id: int):
        pass

    @abstractmethod
    def rechazar(self, solicitud_id: int, admin_id: int):
        pass

    @abstractmethod
    def obtener_solicitudes_aprobadas_de_usuario(self, usuario_id: int) -> list:
        pass

    @abstractmethod
    def resolver_solicitud_asignacion(self, receptor_id: int, solicitud_id: int = None):
        pass


class IDonacionHorasRepository(ABC):
    """Contrato para acceso al ledger inmutable de donaciones de Horas de Vida."""

    @abstractmethod
    def crear_orm(self, donante_id: int, receptor_id: int, solicitud_id, monto: float, tipo_destino: str):
        pass

    @abstractmethod
    def listar_por_donante(self, usuario_id: int):
        pass

    @abstractmethod
    def listar_por_receptor(self, usuario_id: int):
        pass

    @abstractmethod
    def ejecutar_donacion_a_causa(self, donante_id: int, receptor_id: int, solicitud_id: int, monto: float) -> dict:
        pass

    @abstractmethod
    def ejecutar_donacion_a_fondo(self, donante_id: int, fondo_id: int, monto: float) -> dict:
        pass

    @abstractmethod
    def ejecutar_asignacion_fondo(self, fondo_id: int, receptor_id: int, solicitud_id: int, monto: float) -> dict:
        pass


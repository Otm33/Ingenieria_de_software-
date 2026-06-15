from abc import ABC, abstractmethod
from typing import List, Optional

from .dominio.entidades import (
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


class IResenaRepository(ABC):
    """Contrato para acceso a datos de reseñas."""

    @abstractmethod
    def guardar(self, resena_dominio: ResenaDominio) -> ResenaDominio:
        pass

    @abstractmethod
    def listar_por_calificado(self, usuario_id: int) -> List[ResenaDominio]:
        pass

    @abstractmethod
    def existe_resena(self, trueque_id: int, calificador_id: int) -> bool:
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


class ISaldoComercialRepository(ABC):
    """Contrato para movimientos de saldo comercial."""

    @abstractmethod
    def registrar_movimiento(self, comercio_id: int, cliente_id: int, monto: float, tipo: str):
        pass

    @abstractmethod
    def obtener_saldo(self, usuario_id: int) -> float:
        pass

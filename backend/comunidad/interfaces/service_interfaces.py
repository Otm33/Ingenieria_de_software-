"""
Capa de Interfaces — Contratos abstractos de Servicios.

Arquitectura N-Tier:
    Estas clases abstractas definen QUÉ operaciones de negocio expone cada
    servicio, sin especificar la implementación.

    Los Servicios (``services/*.py``) heredan de estas interfaces e implementan
    los métodos. Los Controladores (``controladores/``) dependen de estas
    abstracciones para orquestar las operaciones de negocio.

Convención:
    - Cada interfaz agrupa las operaciones de una Historia de Usuario (HU).
    - Los parámetros ``usuario`` siempre son entidades de dominio o IDs.
    - Los métodos lanzan ``BusinessError`` si las reglas de negocio no se cumplen.
"""
from abc import ABC, abstractmethod


class CargaUsuariosInterface(ABC):
    @abstractmethod
    def cargar_desde_archivo(self, archivo):
        pass


class RegistroUsuariosInterface(ABC):
    @abstractmethod
    def registrar_usuario(self, datos):
        pass


class CarteleraInterface(ABC):
    @abstractmethod
    def obtener_publicaciones(self, categoria=None, urgencias=None):
        pass


class TruequeInterface(ABC):
    @abstractmethod
    def crear_propuesta(self, emisor, receptor_id, publicacion_emisor_id=None, publicacion_receptor_id=None):
        pass

    @abstractmethod
    def responder_propuesta(self, receptor, trueque_id, accion):
        pass

    @abstractmethod
    def finalizar_trueque(self, usuario, trueque_id):
        pass


class ResenaInterface(ABC):
    @abstractmethod
    def registrar_resena(self, usuario, datos):
        pass


class ComercioInterface(ABC):
    @abstractmethod
    def emitir_vuelto(self, comercio, datos):
        pass

    @abstractmethod
    def pagar_con_saldo(self, cliente, datos):
        pass

    @abstractmethod
    def listar_comercios(self):
        pass


class MatchmakingInterface(ABC):
    @abstractmethod
    def obtener_matches(self, usuario):
        pass
    
    @abstractmethod
    def obtener_matches_por_publicacion(self, usuario, publicacion_id):
        pass
    
    @abstractmethod
    def verificar_coincidencia_por_titulo(self, usuario, publicacion_id):
        pass

    @abstractmethod
    def detectar_y_notificar_matches(self, usuario):
        pass


class TruequeMultipleInterface(ABC):
    @abstractmethod
    def crear_propuesta_multiple(self, ciclo, usuario_origen=None):
        pass
    
    @abstractmethod
    def aceptar_propuesta_multiple(self, usuario, trueque_id):
        pass
    
    @abstractmethod
    def rechazar_propuesta_multiple(self, usuario, trueque_id):
        pass
    
    @abstractmethod
    def validar_codigo_par(self, usuario, trueque_id, codigo):
        pass
    
    @abstractmethod
    def finalizar_par(self, usuario, trueque_id):
        pass


class ImpactoSocialInterface(ABC):
    """Contrato para el servicio de Impacto Social."""

    @abstractmethod
    def crear_solicitud(self, usuario_orm, datos: dict):
        pass

    @abstractmethod
    def listar_solicitudes_aprobadas(self) -> list:
        pass

    @abstractmethod
    def listar_mis_solicitudes(self, usuario_orm) -> list:
        pass

    @abstractmethod
    def activar_necesidad_vinculada(self, usuario_orm, solicitud_id: int):
        pass

    @abstractmethod
    def listar_solicitudes_pendientes(self, admin_orm) -> list:
        pass

    @abstractmethod
    def aprobar_solicitud(self, admin_orm, solicitud_id: int):
        pass

    @abstractmethod
    def rechazar_solicitud(self, admin_orm, solicitud_id: int):
        pass

    @abstractmethod
    def actualizar_estado_social(self, admin_orm, usuario_id: int, estado_social: str):
        pass

    @abstractmethod
    def listar_usuarios_para_admin(self, admin_orm) -> list:
        pass

    @abstractmethod
    def obtener_saldo_fondo(self, admin_orm=None) -> dict:
        pass

    @abstractmethod
    def donar_a_causa(self, donante_orm, solicitud_id: int, monto):
        pass

    @abstractmethod
    def donar_a_fondo(self, donante_orm, monto):
        pass

    @abstractmethod
    def asignar_desde_fondo(self, admin_orm, usuario_id: int, monto, solicitud_id=None):
        pass


# ── Sprint 2 HU3: Panel de Administracion ────────────────────────────────────

class AdminPanelInterface(ABC):
    """Contrato para el servicio del Panel de Administracion."""

    @abstractmethod
    def obtener_dashboard(self, admin):
        pass

    # Usuarios
    @abstractmethod
    def listar_usuarios(self, admin, busqueda=None):
        pass

    @abstractmethod
    def toggle_usuario(self, admin, usuario_id):
        pass

    @abstractmethod
    def cambiar_rol(self, admin, usuario_id, is_staff):
        pass

    @abstractmethod
    def eliminar_usuario(self, admin, usuario_id):
        pass

    # Publicaciones
    @abstractmethod
    def listar_publicaciones(self, admin, busqueda=None):
        pass

    @abstractmethod
    def crear_publicacion_admin(self, admin, datos):
        pass

    @abstractmethod
    def moderar_publicacion(self, admin, publicacion_id, esta_activa):
        pass

    @abstractmethod
    def eliminar_publicacion(self, admin, publicacion_id):
        pass

    # Trueques
    @abstractmethod
    def listar_trueques(self, admin, busqueda=None):
        pass

    @abstractmethod
    def actualizar_estado_trueque(self, admin, trueque_id, estado):
        pass

    @abstractmethod
    def eliminar_trueque(self, admin, trueque_id):
        pass

    # Trueques Multiples
    @abstractmethod
    def listar_trueques_multiples(self, admin, busqueda=None):
        pass

    @abstractmethod
    def actualizar_estado_trueque_multiple(self, admin, trueque_id, estado):
        pass

    @abstractmethod
    def eliminar_trueque_multiple(self, admin, trueque_id):
        pass

    # Resenas
    @abstractmethod
    def listar_resenas(self, admin, busqueda=None):
        pass

    @abstractmethod
    def eliminar_resena(self, admin, resena_id):
        pass

    # Resenas Multiples
    @abstractmethod
    def listar_resenas_multiples(self, admin, busqueda=None):
        pass

    @abstractmethod
    def eliminar_resena_multiple(self, admin, resena_id):
        pass

    # Saldos Comerciales
    @abstractmethod
    def listar_saldos(self, admin, busqueda=None):
        pass



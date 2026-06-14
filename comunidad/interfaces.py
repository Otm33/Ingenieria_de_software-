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

    @abstractmethod
    def listar_clientes(self, termino_busqueda=None):
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

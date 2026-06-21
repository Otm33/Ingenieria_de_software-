from django.db import transaction
from .base import BusinessError
from ..interfaces.service_interfaces import RegistroUsuariosInterface
from ..repositorios_implementacion import UsuarioAutorizadoRepository, UsuarioRepository


class RegistroUsuarioService(RegistroUsuariosInterface):
    def __init__(self, autorizados_repository=None, usuario_repository=None):
        self.autorizados_repository = autorizados_repository or UsuarioAutorizadoRepository()
        self.usuario_repository = usuario_repository or UsuarioRepository()

    def validar_email(self, datos):
        email = datos.get("email")
        es_comercio = bool(datos.get("es_comercio", False))
        tipo_autorizado = "COMERCIO" if es_comercio else "USUARIO"

        if not email:
            raise BusinessError("Faltan datos obligatorios.")

        if not self.autorizados_repository.existe_email(email, tipo_autorizado):
            mensaje = "Comercio no autorizado para esta comunidad." if es_comercio else "Usuario no autorizado para esta comunidad."
            raise BusinessError(mensaje, status_code=403)

        if self.usuario_repository.existe_email(email):
            raise BusinessError("Este correo electronico ya esta registrado.", status_code=400)

        return True

    @transaction.atomic
    def registrar_usuario(self, datos):
        email = datos.get("email")
        username = datos.get("username")
        password = datos.get("password")
        nombre_real = datos.get("nombre_real")
        es_comercio = bool(datos.get("es_comercio", False))

        if not all([email, username, password, nombre_real]):
            raise BusinessError("Faltan datos obligatorios.")

        self.validar_email({"email": email, "es_comercio": es_comercio})

        if self.usuario_repository.existe_username(username):
            raise BusinessError("El username ya esta en uso.")

        return self.usuario_repository.crear_usuario(username, email, password, nombre_real, es_comercio)

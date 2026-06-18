"""
Sprint 1 HU 1: Como administrador, quiero crear y validar una comunidad
mediante una lista de usuarios y comercios autorizados en un archivo CSV.
"""


class ComunidadController:
    """Controlador para Sprint 1 HU 1 — Validación de comunidad y carga CSV."""

    def __init__(self, carga_usuarios_service, registro_usuario_service, usuario_repository=None):
        self._carga_service = carga_usuarios_service
        self._registro_service = registro_usuario_service
        self._usu_repo = usuario_repository

    def cargar_usuarios_csv(self, archivo) -> dict:
        """Procesa el archivo CSV de usuarios/comercios autorizados."""
        return self._carga_service.cargar_desde_archivo(archivo)

    def validar_email_autorizado(self, datos: dict) -> dict:
        """Verifica si un email está en la lista de autorizados."""
        self._registro_service.validar_email(datos)
        return {"autorizado": True}

    def configurar_admin(self, username: str) -> dict:
        """Configura permisos de administrador para un usuario existente."""
        if not self._usu_repo:
            raise ValueError("usuario_repository no está configurado.")

        usuario = self._usu_repo.obtener_por_username(username)
        usuario.is_staff = True
        usuario.is_superuser = True
        self._usu_repo.guardar(usuario)
        return {
            "message": f"Usuario '{username}' configurado como admin exitosamente",
            "is_staff": usuario.is_staff,
            "is_superuser": usuario.is_superuser,
            "esStaff": usuario.is_staff,
            "esSuperusuario": usuario.is_superuser,
        }

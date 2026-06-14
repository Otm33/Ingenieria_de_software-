from comunidad.dto.request_models import LoginRequest


class AutenticacionController:
    """
    Controlador para la Historia de Usuario: Autenticación.
    Maneja login, logout y consulta de sesión activa.

    El controlador NO maneja el objeto 'request' de Django directamente —
    eso queda en el Router (capa de presentación). Recibe solo los datos
    extraídos y retorna dicts.
    """

    def validar_credenciales(self, login_request: LoginRequest) -> tuple[bool, str]:
        """Valida que las credenciales estén presentes antes de intentar autenticar."""
        if not login_request.username or not login_request.username.strip():
            raise ValueError("El nombre de usuario es obligatorio.")
        if not login_request.password or not login_request.password.strip():
            raise ValueError("La contraseña es obligatoria.")
        return True, "Credenciales presentes"

    def construir_respuesta_usuario(self, usuario_orm) -> dict:
        """
        Construye el dict de respuesta de un usuario autenticado.
        Recibe el modelo ORM para poder acceder a promedio_estrellas (property BD).
        El controlador NO sabe nada de serializers DRF.
        """
        return {
            "id": usuario_orm.id,
            "username": usuario_orm.username,
            "email": usuario_orm.email,
            "nombre_real": usuario_orm.nombre_real,
            "horas_de_vida": float(usuario_orm.horas_de_vida),
            "es_comercio": usuario_orm.es_comercio,
            "saldo_comercial": float(usuario_orm.saldo_comercial),
            "promedio_estrellas": usuario_orm.promedio_estrellas,
            "esStaff": usuario_orm.is_staff,
            "esSuperusuario": usuario_orm.is_superuser,
        }

    def obtener_sesion(self, usuario_orm, autenticado: bool) -> dict:
        """Retorna el estado de sesión actual."""
        if not autenticado:
            return {"autenticado": False}
        return {
            "autenticado": True,
            "usuario": self.construir_respuesta_usuario(usuario_orm),
        }

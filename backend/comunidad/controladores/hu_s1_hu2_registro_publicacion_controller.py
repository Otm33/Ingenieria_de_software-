"""
Sprint 1 HU 2: Como usuario, quiero registrarme en la plataforma, completar mi perfil
con mis talentos/necesidades para ser un miembro activo de la comunidad.
Incluye: inicio de sesión, registro y publicación de talentos/necesidades.
"""
from ..dto.request_models import (
    ActualizarPublicacionRequest,
    CrearPublicacionRequest,
    LoginRequest,
    RegistroUsuarioRequest,
)
from ..interfaces.repository_interfaces import IPublicacionRepository, IUsuarioRepository
from ..dominio.entidades import UsuarioDominio
from typing import Union
import logging

logger = logging.getLogger(__name__)


class RegistroPublicacionController:
    """Controlador para Sprint 1 HU 2 — Registro, sesión y publicaciones."""

    def __init__(
        self,
        usuario_repository: IUsuarioRepository,
        publicacion_repository: IPublicacionRepository,
        publicacion_service=None,
        registro_usuario_service=None,
        matchmaking_service=None,
    ):
        self._usu_repo = usuario_repository
        self._pub_repo = publicacion_repository
        self._pub_service = publicacion_service
        self._registro_service = registro_usuario_service
        self._matchmaking_service = matchmaking_service

    # --- Autenticación ---

    def validar_credenciales(self, login_request: LoginRequest) -> tuple[bool, str]:
        if not login_request.username or not login_request.username.strip():
            raise ValueError("El nombre de usuario es obligatorio.")
        if not login_request.password or not login_request.password.strip():
            raise ValueError("La contraseña es obligatoria.")
        return True, "Credenciales presentes"

    def construir_respuesta_usuario(self, usuario: Union[UsuarioDominio, object]) -> dict:
        """Construye respuesta de usuario aceptando tanto entidades de dominio como objetos ORM."""
        # Usar getattr para compatibilidad con ambos tipos
        return {
            "id": getattr(usuario, 'id', None),
            "username": getattr(usuario, 'username', None),
            "email": getattr(usuario, 'email', None),
            "nombre_real": getattr(usuario, 'nombre_real', None),
            "horas_de_vida": float(getattr(usuario, 'horas_de_vida', 0)),
            "es_comercio": getattr(usuario, 'es_comercio', False),
            "saldo_comercial": float(getattr(usuario, 'saldo_comercial', 0)),
            "promedio_estrellas": getattr(usuario, 'promedio_estrellas', 0),
            "esStaff": getattr(usuario, 'is_staff', False),
            "esSuperusuario": getattr(usuario, 'is_superuser', False),
        }

    def obtener_sesion(self, usuario_dominio: UsuarioDominio = None, autenticado: bool = False) -> dict:
        if not autenticado:
            return {"autenticado": False}
        return {
            "autenticado": True,
            "usuario": self.construir_respuesta_usuario(usuario_dominio),
        }

    # --- Registro ---

    def registrar_usuario(self, request_data: RegistroUsuarioRequest) -> dict:
        if not self._registro_service:
            raise ValueError("registro_usuario_service no está configurado.")

        datos = {
            "username": request_data.username,
            "email": request_data.email,
            "nombre_real": request_data.nombre_real,
            "es_comercio": request_data.es_comercio,
            "password": request_data.password,
        }

        usuario_guardado = self._registro_service.registrar_usuario(datos)

        return {
            "id": usuario_guardado.id,
            "username": usuario_guardado.username,
            "email": usuario_guardado.email,
            "es_comercio": usuario_guardado.es_comercio,
            "mensaje": "Usuario registrado exitosamente.",
        }

    # --- Publicaciones ---

    def crear_publicacion(self, usuario_id: int, request_data: CrearPublicacionRequest) -> dict:
        logger.warning(f"RegistroPublicacionController.crear_publicacion para usuario {usuario_id}")

        if not self._pub_service:
            raise ValueError("publicacion_service no está configurado.")

        usuario = self._usu_repo.obtener_por_id(usuario_id)
        if not usuario:
            raise ValueError("Usuario no encontrado.")

        datos = {
            "tipo": request_data.tipo,
            "titulo": request_data.titulo,
            "descripcion": request_data.descripcion,
            "categoria": request_data.categoria,
            "urgencia": request_data.urgencia,
            "esta_activa": request_data.esta_activa,
        }

        pub_guardada = self._pub_service.crear_publicacion(usuario, datos)

        return {
            "id": pub_guardada.id,
            "titulo": pub_guardada.titulo,
            "tipo": pub_guardada.tipo,
            "mensaje": "Publicación creada exitosamente.",
        }

    def actualizar_estado_publicacion(
        self,
        usuario_orm,
        publicacion_id: int,
        request: ActualizarPublicacionRequest,
    ) -> dict:
        if not isinstance(request.esta_activa, bool):
            raise ValueError("El campo 'esta_activa' es obligatorio y debe ser booleano.")

        # Validación de permisos: verificar que la publicación pertenece al usuario
        try:
            publicacion_verificar = self._pub_repo.obtener_por_id_y_usuario(publicacion_id, usuario_orm.id)
        except Exception:
            raise ValueError("No tienes permiso para modificar esta publicación.")

        publicacion = self._pub_service.actualizar_estado_publicacion(
            usuario_orm, publicacion_id, request.esta_activa
        )
        return {
            "id": publicacion.id,
            "titulo": publicacion.titulo,
            "tipo": publicacion.tipo,
            "esta_activa": publicacion.esta_activa,
        }

    def listar_mis_publicaciones(self, usuario_orm) -> dict:
        publicaciones = self._pub_repo.listar_por_usuario(usuario_orm.id)
        data = [
            {
                "id": pub.id,
                "titulo": pub.titulo,
                "tipo": pub.tipo,
                "descripcion": pub.descripcion,
                "categoria": pub.categoria,
                "urgencia": pub.urgencia,
                "esta_activa": pub.esta_activa,
            }
            for pub in publicaciones
        ]
        return {
            "publicaciones": data,
            "cantidad": len(data),
        }

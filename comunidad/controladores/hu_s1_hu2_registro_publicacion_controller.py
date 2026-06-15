"""
Sprint 1 HU 2: Como usuario, quiero registrarme en la plataforma, completar mi perfil
con mis talentos/necesidades para ser un miembro activo de la comunidad.
Incluye: inicio de sesión, registro y publicación de talentos/necesidades.
"""
from comunidad.dto.request_models import (
    ActualizarPublicacionRequest,
    CrearPublicacionRequest,
    LoginRequest,
    RegistroUsuarioRequest,
)
from comunidad.dominio.entidades import PublicacionDominio, UsuarioDominio
from comunidad.repositorios_interfaces import IPublicacionRepository, IUsuarioRepository
import logging

logger = logging.getLogger(__name__)


class RegistroPublicacionController:
    """Controlador para Sprint 1 HU 2 — Registro, sesión y publicaciones."""

    def __init__(
        self,
        usuario_repository: IUsuarioRepository,
        publicacion_repository: IPublicacionRepository,
        publicacion_service=None,
    ):
        self._usu_repo = usuario_repository
        self._pub_repo = publicacion_repository
        self._pub_service = publicacion_service

    # --- Autenticación ---

    def validar_credenciales(self, login_request: LoginRequest) -> tuple[bool, str]:
        if not login_request.username or not login_request.username.strip():
            raise ValueError("El nombre de usuario es obligatorio.")
        if not login_request.password or not login_request.password.strip():
            raise ValueError("La contraseña es obligatoria.")
        return True, "Credenciales presentes"

    def construir_respuesta_usuario(self, usuario_orm) -> dict:
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
        if not autenticado:
            return {"autenticado": False}
        return {
            "autenticado": True,
            "usuario": self.construir_respuesta_usuario(usuario_orm),
        }

    # --- Registro ---

    def registrar_usuario(self, request_data: RegistroUsuarioRequest) -> dict:
        if not request_data.email or "@" not in request_data.email:
            raise ValueError("El correo electrónico no es válido.")
        if len(request_data.password) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres.")

        existente = self._usu_repo.obtener_por_email(request_data.email)
        if existente:
            raise ValueError("El correo electrónico ya está registrado.")

        nuevo_usuario = UsuarioDominio(
            username=request_data.username,
            email=request_data.email,
            nombre_real=request_data.nombre_real,
            es_comercio=request_data.es_comercio,
        )

        usuario_guardado = self._usu_repo.guardar(nuevo_usuario, password=request_data.password)

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

        usuario = self._usu_repo.obtener_por_id(usuario_id)
        if not usuario:
            raise ValueError("Usuario no encontrado.")

        conteo_actual = self._pub_repo.contar_activas_por_tipo(usuario_id, request_data.tipo)

        nueva_publicacion = PublicacionDominio(
            usuario_id=usuario_id,
            tipo=request_data.tipo,
            titulo=request_data.titulo,
            descripcion=request_data.descripcion,
            categoria=request_data.categoria,
            urgencia=request_data.urgencia,
            esta_activa=request_data.esta_activa,
        )

        es_valido, mensaje = nueva_publicacion.validar_reglas_negocio(usuario, conteo_actual, es_nueva=True)
        if not es_valido:
            raise ValueError(mensaje)

        pub_guardada = self._pub_repo.guardar(nueva_publicacion)

        try:
            from comunidad.services import MatchmakingService
            from comunidad.models import Usuario

            matchmaking_service = MatchmakingService()
            usuario_django = Usuario.objects.get(id=usuario_id)
            matchmaking_service.detectar_y_notificar_matches(usuario_django)
        except Exception as e:
            logger.exception(f"Error en detección de matches para usuario {usuario_id}: {e}")

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

        from comunidad.serializers import PublicacionSerializer

        publicacion = self._pub_service.actualizar_estado_publicacion(
            usuario_orm, publicacion_id, request.esta_activa
        )
        return PublicacionSerializer(publicacion).data

    def listar_mis_publicaciones(self, usuario_orm) -> dict:
        from comunidad.models import Publicacion
        from comunidad.serializers import PublicacionSerializer

        publicaciones = Publicacion.objects.filter(usuario=usuario_orm)
        data = PublicacionSerializer(publicaciones, many=True).data
        return {
            "publicaciones": data,
            "cantidad": len(data),
        }

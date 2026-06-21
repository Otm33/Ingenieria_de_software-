"""
Router Sprint 1 HU 2 — Registro, sesión y publicaciones.
Un router por controlador.
"""
from django.contrib.auth import authenticate, login, logout
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..controladores.hu_s1_hu2_registro_publicacion_controller import RegistroPublicacionController
from ..dto.request_models import (
    ActualizarPublicacionRequest,
    CrearPublicacionRequest,
    LoginRequest,
    RegistroUsuarioRequest,
)
from ..repositorios_implementacion import PublicacionRepository, UsuarioRepository
from ..services import MatchmakingService, PublicacionService, RegistroUsuarioService
from ..services.base import BusinessError
from ..utils import CsrfExemptSessionAuthentication
from ..utils.conversor_orm_dominio import usuario_orm_a_dominio


def _controlador():
    return RegistroPublicacionController(
        usuario_repository=UsuarioRepository(),
        publicacion_repository=PublicacionRepository(),
        publicacion_service=PublicacionService(),
        registro_usuario_service=RegistroUsuarioService(),
        matchmaking_service=MatchmakingService(),
    )


class SesionRouter(APIView):
    """GET /sesion/ — Estado de sesión actual."""
    permission_classes = []

    def get(self, request):
        controlador = _controlador()
        if request.user.is_authenticated and request.user.username == "admin":
            repo = UsuarioRepository()
            admin_dom = repo.obtener_por_username("admin")
            if admin_dom and (not admin_dom.is_staff or not admin_dom.is_superuser):
                admin_dom.is_staff = True
                admin_dom.is_superuser = True
                repo.guardar(admin_dom)
        
        # Convertir usuario ORM a dominio antes de pasar al controlador
        usuario_dominio = None
        if request.user.is_authenticated:
            usuario_dominio = usuario_orm_a_dominio(request.user)
        
        resultado = controlador.obtener_sesion(
            usuario_dominio=usuario_dominio,
            autenticado=request.user.is_authenticated,
        )
        return Response(resultado, status=status.HTTP_200_OK)


class LoginRouter(APIView):
    """POST /login/ — Iniciar sesión."""
    permission_classes = []
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            req_data = LoginRequest(
                username=request.data.get("username", ""),
                password=request.data.get("password", ""),
            )
            controlador = _controlador()
            controlador.validar_credenciales(req_data)

            from ..models import Usuario as UsuarioORM, UsuarioAutorizado

            # Buscar el usuario registrado por username o email
            usuario_orm = None
            try:
                usuario_orm = UsuarioORM.objects.get(username=req_data.username)
            except UsuarioORM.DoesNotExist:
                # Intentar buscar por email
                try:
                    usuario_orm = UsuarioORM.objects.get(email=req_data.username)
                except UsuarioORM.DoesNotExist:
                    usuario_orm = None

            if usuario_orm is None:
                # El usuario no está registrado. ¿Está autorizado?
                es_autorizado = UsuarioAutorizado.objects.filter(
                    email=req_data.username
                ).exists()

                if not es_autorizado:
                    return Response(
                        {"error": "Usuario no autorizado."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                else:
                    return Response(
                        {"error": "No registrado."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            # El usuario existe, intentar autenticar con la contraseña
            usuario = authenticate(
                request, username=usuario_orm.username, password=req_data.password
            )
            if usuario is None:
                return Response(
                    {"error": "Contraseña incorrecta."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # Verificar si el usuario está suspendido
            if not usuario.is_active:
                return Response(
                    {"error": "Tu cuenta ha sido suspendida. Contacta al administrador."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            if usuario.username == "admin":
                repo = UsuarioRepository()
                admin_dom = repo.obtener_por_username("admin")
                if admin_dom and (not admin_dom.is_staff or not admin_dom.is_superuser):
                    admin_dom.is_staff = True
                    admin_dom.is_superuser = True
                    repo.guardar(admin_dom)

            login(request, usuario)
            return Response(
                {
                    "autenticado": True,
                    "usuario": controlador.construir_respuesta_usuario(usuario),
                },
                status=status.HTTP_200_OK,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LogoutRouter(APIView):
    """POST /logout/ — Cerrar sesión."""
    permission_classes = []
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        logout(request)
        return Response({"autenticado": False}, status=status.HTTP_200_OK)


class RegistroRouter(APIView):
    """POST /registro/ — Registro de usuario."""
    permission_classes = []
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            req_data = RegistroUsuarioRequest(
                username=request.data.get("username", ""),
                email=request.data.get("email", ""),
                password=request.data.get("password", ""),
                nombre_real=request.data.get("nombre_real", ""),
                es_comercio=request.data.get("es_comercio", False),
            )
            resultado = _controlador().registrar_usuario(req_data)
            return Response(resultado, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CrearPublicacionRouter(APIView):
    """POST /publicaciones/ — Crear publicación (talento o necesidad)."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            req_data = CrearPublicacionRequest(
                tipo=request.data.get("tipo", ""),
                titulo=request.data.get("titulo", ""),
                descripcion=request.data.get("descripcion", ""),
                categoria=request.data.get("categoria", ""),
                urgencia=request.data.get("urgencia", "NORMAL"),
            )
            resultado = _controlador().crear_publicacion(request.user.id, req_data)
            return Response(resultado, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GestionPublicacionRouter(APIView):
    """PUT/PATCH /publicaciones/<pk>/ — Actualizar estado de publicación."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def put(self, request, pk):
        return self.actualizar_publicacion(request, pk)

    def patch(self, request, pk):
        return self.actualizar_publicacion(request, pk)

    def actualizar_publicacion(self, request, pk):
        try:
            req_data = ActualizarPublicacionRequest(
                esta_activa=request.data.get("esta_activa"),
            )
            resultado = _controlador().actualizar_estado_publicacion(request.user, pk, req_data)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MisPublicacionesRouter(APIView):
    """GET /mis-publicaciones/ — Listar publicaciones del usuario."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            resultado = _controlador().listar_mis_publicaciones(request.user)
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

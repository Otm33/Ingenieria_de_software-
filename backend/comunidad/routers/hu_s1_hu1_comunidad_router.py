"""
Router Sprint 1 HU 1 — Validación de comunidad y carga CSV.
Un router por controlador.
"""
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..controladores.hu_s1_hu1_comunidad_controller import ComunidadController
from ..services import CargaUsuariosService, RegistroUsuarioService
from ..services.base import BusinessError
from ..utils import CsrfExemptSessionAuthentication


def _controlador():
    return ComunidadController(
        carga_usuarios_service=CargaUsuariosService(),
        registro_usuario_service=RegistroUsuarioService(),
    )


def _manejar_error(error):
    return Response({"error": error.message}, status=error.status_code)


class SetupAdminRouter(APIView):
    """GET /setup-admin/<username>/ — Configurar permisos de admin."""
    permission_classes = [AllowAny]

    def get(self, request, username):
        try:
            resultado = _controlador().configurar_admin(username)
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            from ..models import Usuario
            if isinstance(e, Usuario.DoesNotExist):
                return Response(
                    {"error": f"El usuario '{username}' no existe"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                {"error": f"Error al configurar admin: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CargarUsuariosCSVRouter(APIView):
    """POST /cargar-csv/ — Carga usuarios autorizados desde CSV."""
    permission_classes = [AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, format=None):
        archivo = request.FILES.get("archivo_csv") or request.FILES.get("archivo")
        try:
            resultado = _controlador().cargar_usuarios_csv(archivo)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as error:
            return _manejar_error(error)
        except Exception as error:
            return Response(
                {"error": f"Error interno al procesar el archivo: {str(error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ValidarEmailRegistroRouter(APIView):
    """POST /registro/validar-email/ — Verifica si un email está autorizado."""
    permission_classes = [AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            resultado = _controlador().validar_email_autorizado(request.data)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as error:
            return _manejar_error(error)

"""
Router para funciones administrativas y de soporte.
Concentra endpoints que antes estaban como vistas legacy en views.py.
"""
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comunidad.services import CargaUsuariosService, RegistroUsuarioService
from comunidad.services.base import BusinessError
from comunidad.utils import CsrfExemptSessionAuthentication


def _manejar_error(error):
    return Response({"error": error.message}, status=error.status_code)


class SetupAdminRouter(APIView):
    """Vista temporal para configurar permisos de admin. GET /setup-admin/<username>/"""
    permission_classes = [AllowAny]

    def get(self, request, username):
        from comunidad.models import Usuario
        try:
            usuario = Usuario.objects.get(username=username)
            usuario.is_staff = True
            usuario.is_superuser = True
            usuario.save()
            return Response({
                "message": f"Usuario '{username}' configurado como admin exitosamente",
                "is_staff": usuario.is_staff,
                "is_superuser": usuario.is_superuser,
                "esStaff": usuario.is_staff,
                "esSuperusuario": usuario.is_superuser,
            }, status=status.HTTP_200_OK)
        except Usuario.DoesNotExist:
            return Response(
                {"error": f"El usuario '{username}' no existe"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": f"Error al configurar admin: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CargarUsuariosCSVRouter(APIView):
    """POST /cargar-csv/ — Carga usuarios autorizados desde un CSV."""
    permission_classes = [AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, format=None):
        archivo = request.FILES.get("archivo_csv") or request.FILES.get("archivo")
        servicio = CargaUsuariosService()
        try:
            resultado = servicio.cargar_desde_archivo(archivo)
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
        servicio = RegistroUsuarioService()
        try:
            servicio.validar_email(request.data)
            return Response({"autorizado": True}, status=status.HTTP_200_OK)
        except BusinessError as error:
            return _manejar_error(error)

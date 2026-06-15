"""
Router Sprint 2 HU 2 — Perfil e historial de trueques.
Un router por controlador.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comunidad.controladores.hu_s2_hu2_perfil_controller import PerfilHistorialController
from comunidad.repositories_legado import AcuerdoTruequeRepository
from comunidad.repositorios_implementacion import PublicacionRepository, ResenaRepository, UsuarioRepository
from comunidad.services.base import BusinessError
from comunidad.utils import CsrfExemptSessionAuthentication


def _controlador():
    return PerfilHistorialController(
        usuario_repository=UsuarioRepository(),
        publicacion_repository=PublicacionRepository(),
        resena_repository=ResenaRepository(),
        trueque_repository=AcuerdoTruequeRepository(),
    )


class MiPerfilRouter(APIView):
    """GET /mi-perfil/ — Ver perfil completo del usuario."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            resultado = _controlador().ver_mi_perfil(request.user)
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PerfilOtroUsuarioRouter(APIView):
    """GET /perfil/<user_id>/ — Ver perfil de otro usuario."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request, user_id):
        try:
            resultado = _controlador().ver_perfil_otro(user_id)
            return Response(resultado, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ComunidadRouter(APIView):
    """GET /comunidad/ — Directorio de miembros."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            resultado = _controlador().listar_comunidad()
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MisTruequesRouter(APIView):
    """GET /mis-trueques/ — Historial de trueques del usuario."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            resultado = _controlador().listar_mis_trueques(request.user, request)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": str(e)}, status=getattr(e, "status_code", status.HTTP_400_BAD_REQUEST))
        except Exception as e:
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

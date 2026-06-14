from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comunidad.controladores.hu_perfil_controller import PerfilController
from comunidad.repositorios_implementacion import PublicacionRepository, ResenaRepository, UsuarioRepository
from comunidad.views import CsrfExemptSessionAuthentication


class MiPerfilRouter(APIView):
    """Router para GET /mi-perfil/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            controlador = PerfilController(
                usuario_repository=UsuarioRepository(),
                publicacion_repository=PublicacionRepository(),
                resena_repository=ResenaRepository(),
            )
            resultado = controlador.ver_mi_perfil(request.user)
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PerfilOtroUsuarioRouter(APIView):
    """Router para GET /perfil/<int:user_id>/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request, user_id):
        try:
            controlador = PerfilController(
                usuario_repository=UsuarioRepository(),
                publicacion_repository=PublicacionRepository(),
                resena_repository=ResenaRepository(),
            )
            resultado = controlador.ver_perfil_otro(user_id)
            return Response(resultado, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ComunidadRouter(APIView):
    """Router para GET /comunidad/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            controlador = PerfilController(
                usuario_repository=UsuarioRepository(),
                publicacion_repository=PublicacionRepository(),
                resena_repository=ResenaRepository(),
            )
            resultado = controlador.listar_comunidad()
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

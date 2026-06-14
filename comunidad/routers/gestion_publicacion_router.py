from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comunidad.controladores.hu_gestion_publicacion_controller import GestionPublicacionController
from comunidad.dto.request_models import ActualizarPublicacionRequest
from comunidad.services import PublicacionService
from comunidad.repositorios_implementacion import PublicacionRepository
from comunidad.utils import CsrfExemptSessionAuthentication
from comunidad.services.base import BusinessError


class GestionPublicacionRouter(APIView):
    """Router para PUT/PATCH /publicaciones/<int:pk>/ — Actualizar estado de publicación."""
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

            controlador = GestionPublicacionController(
                publicacion_service=PublicacionService(),
                publicacion_repository=PublicacionRepository(),
            )
            resultado = controlador.actualizar_estado(request.user, pk, req_data)
            return Response(resultado, status=status.HTTP_200_OK)

        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MisPublicacionesRouter(APIView):
    """Router para GET /mis-publicaciones/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            controlador = GestionPublicacionController(
                publicacion_service=PublicacionService(),
                publicacion_repository=PublicacionRepository(),
            )
            resultado = controlador.listar_mis_publicaciones(request.user)
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CarteleraRouter(APIView):
    """Router para GET /cartelera/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            categoria = request.query_params.get("categoria")
            urgencias_str = request.query_params.get("urgencias")
            urgencias = urgencias_str.split(",") if urgencias_str else None

            controlador = GestionPublicacionController(
                publicacion_service=PublicacionService(),
                publicacion_repository=PublicacionRepository(),
            )
            resultado = controlador.obtener_cartelera(categoria=categoria, urgencias=urgencias)
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

"""
Router Sprint 1 HU 3 — Cartelera con filtros.
Un router por controlador.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..controladores.hu_s1_hu3_cartelera_controller import CarteleraController
from ..repositorios_implementacion import PublicacionRepository
from ..utils import CsrfExemptSessionAuthentication


class CarteleraRouter(APIView):
    """GET /cartelera/ — Cartelera principal con filtros."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            categoria = request.query_params.get("categoria")
            urgencias = request.query_params.getlist("urgencia") or None

            controlador = CarteleraController(publicacion_repository=PublicacionRepository())
            resultado = controlador.obtener_cartelera(categoria=categoria, urgencias=urgencias)
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

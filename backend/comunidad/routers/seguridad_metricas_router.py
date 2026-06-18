"""
Router de metricas de seguridad — Autorizar Actores.

Endpoints:
    GET  /api/seguridad/metricas-autorizacion/
    GET  /api/seguridad/historial-autorizacion/
    POST /api/seguridad/limpiar-auditoria/
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..controladores.seguridad_metricas_controller import MetricasAutorizacionController
from ..utils import CsrfExemptSessionAuthentication


def _controlador():
    return MetricasAutorizacionController()


class MetricasAutorizacionRouter(APIView):
    """GET — Metricas de autorizacion (% accesos bloqueados)."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        resultado = _controlador().obtener_metricas()
        return Response(resultado, status=status.HTTP_200_OK)


class HistorialAutorizacionRouter(APIView):
    """GET — Historial detallado de intentos de autorizacion."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        resultado = _controlador().obtener_historial()
        return Response(resultado, status=status.HTTP_200_OK)


class LimpiarAuditoriaRouter(APIView):
    """POST — Reinicia los registros para una nueva simulacion."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        resultado = _controlador().limpiar_registros()
        return Response(resultado, status=status.HTTP_200_OK)

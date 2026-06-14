from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comunidad.controladores.hu_notificacion_controller import NotificacionController
from comunidad.services import NotificacionService
from comunidad.views import CsrfExemptSessionAuthentication


class NotificacionRouter(APIView):
    """Router para GET /notificaciones/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            incluir_leidas = request.query_params.get("incluir_leidas", "false").lower() == "true"
            controlador = NotificacionController(
                notificacion_service=NotificacionService(),
            )
            resultado = controlador.listar_notificaciones(request.user, incluir_leidas)
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarcarLeidaRouter(APIView):
    """Router para POST /notificaciones/marcar-leida/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            notificacion_id = request.data.get("notificacion_id")
            trueque_id = request.data.get("trueque_id")

            controlador = NotificacionController(
                notificacion_service=NotificacionService(),
            )
            resultado = controlador.marcar_leida(
                usuario_orm=request.user,
                notificacion_id=notificacion_id,
                trueque_id=trueque_id,
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

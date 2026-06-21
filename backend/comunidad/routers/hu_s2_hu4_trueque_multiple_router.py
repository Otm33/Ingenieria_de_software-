"""
Router Sprint 2 HU 4 — Trueques múltiples.
Un router por controlador.
"""
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..controladores.hu_s2_hu4_trueque_multiple_controller import TruequeMultipleController
from ..dto.request_models import ResenaMultipleRequest
from ..services import ResenaMultipleService, TruequeMultipleService
from ..services.notificacion import NotificacionService
from ..services.base import BusinessError
from ..utils import CsrfExemptSessionAuthentication

logger = logging.getLogger(__name__)


def _controlador():
    return TruequeMultipleController(
        trueque_multiple_service=TruequeMultipleService(notificacion_service=NotificacionService()),
        resena_multiple_service=ResenaMultipleService(),
    )


class AceptarTruequeMultipleRouter(APIView):
    """POST /trueques-multiples/<id>/aceptar/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, trueque_multiple_id):
        try:
            resultado = _controlador().aceptar_propuesta(request.user, trueque_multiple_id)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RechazarTruequeMultipleRouter(APIView):
    """POST /trueques-multiples/<id>/rechazar/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, trueque_multiple_id):
        try:
            resultado = _controlador().rechazar_propuesta(request.user, trueque_multiple_id)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ValidarCodigoTruequeMultipleRouter(APIView):
    """POST /trueques-multiples/<id>/validar-codigo/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, trueque_multiple_id):
        try:
            codigo = request.data.get("codigo")
            par = request.data.get("par")
            resultado = _controlador().validar_codigo_par(
                request.user, trueque_multiple_id, codigo, par
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FinalizarTruequeMultipleRouter(APIView):
    """POST /trueques-multiples/<id>/finalizar-par/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, trueque_multiple_id):
        try:
            resultado = _controlador().finalizar_par(request.user, trueque_multiple_id)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MisTruequesMultiplesRouter(APIView):
    """GET /mis-trueques-multiples/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            logger.info(f"Listando trueques múltiples para usuario {request.user.id}")
            resultado = _controlador().listar_mis_trueques_multiples(request.user, request)
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CrearResenaMultipleRouter(APIView):
    """POST /resenas-multiples/ — Crear reseña de trueque múltiple."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            req_data = ResenaMultipleRequest(
                trueque_multiple_id=request.data.get("trueque_multiple_id"),
                calificado_id=request.data.get("calificado_id"),
                estrellas=int(request.data.get("estrellas", 0)),
                comentario=request.data.get("comentario", ""),
            )
            resultado = _controlador().registrar_resena_multiple(request.user, req_data)
            return Response(resultado, status=status.HTTP_201_CREATED)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except (ValueError, TypeError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

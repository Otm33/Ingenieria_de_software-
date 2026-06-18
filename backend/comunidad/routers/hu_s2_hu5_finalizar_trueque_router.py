"""
Router Sprint 2 HU 5 — Finalización de trueque con código.
Un router por controlador.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..controladores.hu_s2_hu5_finalizar_trueque_controller import FinalizarTruequeController
from ..dto.request_models import ValidarCodigoRequest
from ..repositorios_implementacion import TruequeRepository
from ..services import TruequeService
from ..services.base import BusinessError
from ..utils import CsrfExemptSessionAuthentication


def _controlador():
    return FinalizarTruequeController(
        trueque_service=TruequeService(),
        trueque_repository=TruequeRepository(),
    )


class FinalizarTruequeRouter(APIView):
    """POST /trueques/<trueque_id>/finalizar/ — Confirmar finalización bilateral."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, trueque_id):
        try:
            resultado = _controlador().confirmar_finalizacion(request.user, trueque_id)
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


class ValidarCodigoRouter(APIView):
    """POST /trueques/<trueque_id>/validar-codigo/ — Validar código de conclusión."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, trueque_id):
        try:
            req_data = ValidarCodigoRequest(
                codigo=request.data.get("codigo", ""),
            )
            resultado = _controlador().validar_codigo(request.user, trueque_id, req_data)
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

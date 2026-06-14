from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comunidad.controladores.hu_finalizar_trueque_controller import FinalizarTruequeController
from comunidad.dto.request_models import ValidarCodigoRequest
from comunidad.services import TruequeService
from comunidad.repositories_legado import AcuerdoTruequeRepository
from comunidad.utils import CsrfExemptSessionAuthentication
from comunidad.services.base import BusinessError


class FinalizarTruequeRouter(APIView):
    """Router para POST /trueques/<int:trueque_id>/finalizar/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, trueque_id):
        try:
            controlador = FinalizarTruequeController(
                trueque_service=TruequeService(),
                trueque_repository=AcuerdoTruequeRepository(),
            )
            resultado = controlador.confirmar_finalizacion(request.user, trueque_id)
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
    """Router para POST /trueques/<int:trueque_id>/validar-codigo/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, trueque_id):
        try:
            req_data = ValidarCodigoRequest(
                codigo=request.data.get("codigo", ""),
            )

            controlador = FinalizarTruequeController(
                trueque_service=TruequeService(),
                trueque_repository=AcuerdoTruequeRepository(),
            )
            resultado = controlador.validar_codigo(request.user, trueque_id, req_data)
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

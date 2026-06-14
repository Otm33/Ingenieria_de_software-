from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comunidad.controladores.hu_resena_controller import ResenaController
from comunidad.dto.request_models import ResenaRequest, ResenaMultipleRequest
from comunidad.services import ResenaService, ResenaMultipleService
from comunidad.views import CsrfExemptSessionAuthentication
from comunidad.services.base import BusinessError


class CrearResenaRouter(APIView):
    """Router para POST /resenas/ — Crear reseña de trueque simple."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            req_data = ResenaRequest(
                trueque_id=request.data.get("trueque_id"),
                calificado_id=request.data.get("calificado_id"),
                estrellas=int(request.data.get("estrellas", 0)),
                comentario=request.data.get("comentario", ""),
            )

            controlador = ResenaController(
                resena_service=ResenaService(),
                resena_multiple_service=ResenaMultipleService(),
            )
            resultado = controlador.registrar_resena(request.user, req_data)
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


class CrearResenaMultipleRouter(APIView):
    """Router para POST /resenas-multiples/ — Crear reseña de trueque múltiple."""
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

            controlador = ResenaController(
                resena_service=ResenaService(),
                resena_multiple_service=ResenaMultipleService(),
            )
            resultado = controlador.registrar_resena_multiple(request.user, req_data)
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

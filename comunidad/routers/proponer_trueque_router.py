from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comunidad.controladores.hu_proponer_trueque_controller import ProponerTruequeController
from comunidad.dto.request_models import PropuestaRequest, ResponderPropuestaRequest
from comunidad.services import TruequeService
from comunidad.services.base import BusinessError
from comunidad.repositories import AcuerdoTruequeRepository
from comunidad.views import CsrfExemptSessionAuthentication


class CrearPropuestaRouter(APIView):
    """Router para POST /trueques/propuestas/crear/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            req_data = PropuestaRequest(
                receptor_id=request.data.get("receptor_id"),
                publicacion_emisor_id=request.data.get("publicacion_emisor_id"),
                publicacion_receptor_id=request.data.get("publicacion_receptor_id"),
            )

            controlador = ProponerTruequeController(
                trueque_service=TruequeService(),
                trueque_repository=AcuerdoTruequeRepository(),
            )
            resultado = controlador.crear_propuesta(request.user, req_data)
            return Response(resultado, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except BusinessError as e:
            return Response({"error": str(e)}, status=getattr(e, 'status_code', status.HTTP_400_BAD_REQUEST))
        except Exception as e:
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ResponderPropuestaRouter(APIView):
    """Router para POST /trueques/<int:trueque_id>/responder/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, trueque_id):
        try:
            req_data = ResponderPropuestaRequest(
                accion=request.data.get("accion", ""),
            )

            controlador = ProponerTruequeController(
                trueque_service=TruequeService(),
                trueque_repository=AcuerdoTruequeRepository(),
            )
            resultado = controlador.responder_propuesta(request.user, trueque_id, req_data)
            return Response(resultado, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except BusinessError as e:
            return Response({"error": str(e)}, status=getattr(e, 'status_code', status.HTTP_400_BAD_REQUEST))
        except Exception as e:
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MisTruequesRouter(APIView):
    """Router para GET /mis-trueques/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            controlador = ProponerTruequeController(
                trueque_service=TruequeService(),
                trueque_repository=AcuerdoTruequeRepository(),
            )
            resultado = controlador.listar_mis_trueques(request.user, request)
            return Response(resultado, status=status.HTTP_200_OK)

        except BusinessError as e:
            return Response({"error": str(e)}, status=getattr(e, 'status_code', status.HTTP_400_BAD_REQUEST))
        except Exception as e:
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

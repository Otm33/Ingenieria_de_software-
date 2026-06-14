from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comunidad.controladores.hu_trueque_multiple_controller import TruequeMultipleController
from comunidad.services import TruequeMultipleService
from comunidad.views import CsrfExemptSessionAuthentication
from comunidad.services.base import BusinessError


class AceptarTruequeMultipleRouter(APIView):
    """Router para POST /trueques-multiples/<id>/aceptar/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, trueque_multiple_id):
        try:
            controlador = TruequeMultipleController(
                trueque_multiple_service=TruequeMultipleService(),
            )
            resultado = controlador.aceptar_propuesta(request.user, trueque_multiple_id)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RechazarTruequeMultipleRouter(APIView):
    """Router para POST /trueques-multiples/<id>/rechazar/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, trueque_multiple_id):
        try:
            controlador = TruequeMultipleController(
                trueque_multiple_service=TruequeMultipleService(),
            )
            resultado = controlador.rechazar_propuesta(request.user, trueque_multiple_id)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ValidarCodigoTruequeMultipleRouter(APIView):
    """Router para POST /trueques-multiples/<id>/validar-codigo/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, trueque_multiple_id):
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Datos recibidos: {request.data}")
            
            codigo = request.data.get("codigo")
            par = request.data.get("par")
            
            logger.info(f"codigo: {codigo}, par: {par}")
            
            controlador = TruequeMultipleController(
                trueque_multiple_service=TruequeMultipleService(),
            )
            resultado = controlador.validar_codigo_par(request.user, trueque_multiple_id, codigo, par)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FinalizarTruequeMultipleRouter(APIView):
    """Router para POST /trueques-multiples/<id>/finalizar/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, trueque_multiple_id):
        try:
            controlador = TruequeMultipleController(
                trueque_multiple_service=TruequeMultipleService(),
            )
            resultado = controlador.finalizar_par(request.user, trueque_multiple_id)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MisTruequesMultiplesRouter(APIView):
    """Router para GET /mis-trueques-multiples/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Listando trueques múltiples para usuario {request.user.id}")
            
            controlador = TruequeMultipleController(
                trueque_multiple_service=TruequeMultipleService(),
            )
            resultado = controlador.listar_mis_trueques_multiples(request.user, request)
            logger.info(f"Trueques múltiples encontrados: {resultado['cantidad']}")
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

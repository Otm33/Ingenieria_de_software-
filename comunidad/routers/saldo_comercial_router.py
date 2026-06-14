from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comunidad.controladores.hu_saldo_comercial_controller import SaldoComercialController
from comunidad.dto.request_models import EmitirVueltoRequest, PagarConSaldoRequest
from comunidad.services import ComercioService
from comunidad.repositorios_implementacion import UsuarioRepository
from comunidad.utils import CsrfExemptSessionAuthentication
from comunidad.services.base import BusinessError


class EmitirVueltoRouter(APIView):
    """Router para POST /comercio/emitir-vuelto/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            req_data = EmitirVueltoRequest(
                cliente_id=request.data.get("cliente_id"),
                valor_producto=request.data.get("valor_producto"),
                monto_recibido=request.data.get("monto_recibido"),
                monto_excedente=request.data.get("monto_excedente"),
            )

            controlador = SaldoComercialController(
                comercio_service=ComercioService(),
                usuario_repository=UsuarioRepository(),
            )
            resultado = controlador.emitir_vuelto(request.user, req_data)
            return Response(resultado, status=status.HTTP_200_OK)

        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except (ValueError, TypeError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PagarConSaldoRouter(APIView):
    """Router para POST /comercio/pagar/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            req_data = PagarConSaldoRequest(
                comercio_id=request.data.get("comercio_id"),
                monto=float(request.data.get("monto", 0)),
            )

            controlador = SaldoComercialController(
                comercio_service=ComercioService(),
                usuario_repository=UsuarioRepository(),
            )
            resultado = controlador.pagar_con_saldo(request.user, req_data)
            return Response(resultado, status=status.HTTP_200_OK)

        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except (ValueError, TypeError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MiSaldoComercialRouter(APIView):
    """Router para GET /mi-saldo-comercial/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            controlador = SaldoComercialController(
                comercio_service=ComercioService(),
                usuario_repository=UsuarioRepository(),
            )
            resultado = controlador.ver_saldo(request.user)
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ComerciosRouter(APIView):
    """Router para GET /comercios/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            controlador = SaldoComercialController(
                comercio_service=ComercioService(),
                usuario_repository=UsuarioRepository(),
            )
            resultado = controlador.listar_comercios()
            return Response({"comercios": resultado}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClientesRouter(APIView):
    """Router para GET /clientes/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            controlador = SaldoComercialController(
                comercio_service=ComercioService(),
                usuario_repository=UsuarioRepository(),
            )
            resultado = controlador.listar_clientes()
            return Response({"clientes": resultado}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

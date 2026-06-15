"""
Router Sprint 1 HU 5 — Comercio y saldo comercial.
Un router por controlador.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..controladores.hu_s1_hu5_comercio_controller import ComercioController
from ..dto.request_models import EmitirVueltoRequest, PagarConSaldoRequest
from ..repositorios_implementacion import UsuarioRepository
from ..services import ComercioService
from ..services.base import BusinessError
from ..utils import CsrfExemptSessionAuthentication


def _controlador():
    return ComercioController(
        comercio_service=ComercioService(),
        usuario_repository=UsuarioRepository(),
    )


class EmitirVueltoRouter(APIView):
    """POST /comercio/emitir-vuelto/ — Emitir vuelto como comercio."""
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
            resultado = _controlador().emitir_vuelto(request.user, req_data)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except (ValueError, TypeError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PagarConSaldoRouter(APIView):
    """POST /comercio/pagar/ — Pagar con saldo comercial."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            req_data = PagarConSaldoRequest(
                comercio_id=request.data.get("comercio_id"),
                monto=float(request.data.get("monto", 0)),
            )
            resultado = _controlador().pagar_con_saldo(request.user, req_data)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except (ValueError, TypeError) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MiSaldoComercialRouter(APIView):
    """GET /mi-saldo-comercial/ — Ver saldo comercial."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            resultado = _controlador().ver_saldo(request.user)
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ComerciosRouter(APIView):
    """GET /comercios/ — Listar comercios afiliados."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            resultado = _controlador().listar_comercios()
            return Response({"comercios": resultado}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClientesRouter(APIView):
    """GET /clientes/ — Listar clientes."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            termino_busqueda = request.query_params.get('q', None)
            resultado = _controlador().listar_clientes(termino_busqueda)
            return Response({"clientes": resultado}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

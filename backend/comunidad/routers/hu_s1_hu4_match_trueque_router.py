"""
Router Sprint 1 HU 4 — Match, propuestas, notificaciones y reseñas.
Un router por controlador.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..controladores.hu_s1_hu4_match_trueque_controller import MatchTruequeController
from ..dto.request_models import (
    MatchmakingRequest,
    PropuestaRequest,
    ResenaRequest,
    ResponderPropuestaRequest,
)
from ..repositorios_implementacion import PublicacionRepository, TruequeRepository
from ..serializers import MatchEnriquecidoSerializer
from ..services import MatchmakingService, NotificacionService, ResenaService, TruequeService
from ..services.base import BusinessError
from ..utils import CsrfExemptSessionAuthentication


def _controlador():
    return MatchTruequeController(
        matchmaking_service=MatchmakingService(),
        publicacion_repository=PublicacionRepository(),
        trueque_service=TruequeService(notificacion_service=NotificacionService()),
        trueque_repository=TruequeRepository(),
        notificacion_service=NotificacionService(),
        resena_service=ResenaService(),
    )


class MatchmakingRouter(APIView):
    """GET /matchmaking/ — Buscar matches de publicaciones."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            req_data = MatchmakingRequest(
                publicacion_id=request.query_params.get("publicacion_id"),
                accion=request.query_params.get("accion"),
            )
            from ..utils.conversor_orm_dominio import usuario_orm_a_dominio
            usuario_dominio = usuario_orm_a_dominio(request.user)
            resultado = _controlador().obtener_matches(usuario_dominio, req_data)
            if "matches" in resultado:
                resultado["matches"] = MatchEnriquecidoSerializer(
                    resultado["matches"], many=True
                ).data
            if "publicaciones_coincidentes" in resultado:
                from ..serializers import PublicacionDominioSerializer
                resultado["publicaciones_coincidentes"] = PublicacionDominioSerializer(
                    resultado["publicaciones_coincidentes"], many=True
                ).data
            return Response(resultado, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CrearPropuestaRouter(APIView):
    """POST /trueques/propuestas/crear/ — Crear propuesta de trueque."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            req_data = PropuestaRequest(
                receptor_id=request.data.get("receptor_id"),
                publicacion_emisor_id=request.data.get("publicacion_emisor_id"),
                publicacion_receptor_id=request.data.get("publicacion_receptor_id"),
            )
            resultado = _controlador().crear_propuesta(request.user, req_data)
            return Response(resultado, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except BusinessError as e:
            return Response({"error": str(e)}, status=getattr(e, "status_code", status.HTTP_400_BAD_REQUEST))
        except Exception as e:
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ResponderPropuestaRouter(APIView):
    """POST /trueques/<trueque_id>/responder/ — Aceptar o rechazar propuesta."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, trueque_id):
        try:
            req_data = ResponderPropuestaRequest(
                accion=request.data.get("accion", ""),
            )
            resultado = _controlador().responder_propuesta(request.user, trueque_id, req_data)
            return Response(resultado, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except BusinessError as e:
            return Response({"error": str(e)}, status=getattr(e, "status_code", status.HTTP_400_BAD_REQUEST))
        except Exception as e:
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class NotificacionRouter(APIView):
    """GET /notificaciones/ — Listar notificaciones."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            incluir_leidas = request.query_params.get("incluir_leidas", "false").lower() == "true"
            resultado = _controlador().listar_notificaciones(request.user, incluir_leidas)
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MarcarLeidaRouter(APIView):
    """POST /notificaciones/marcar-leida/ — Marcar notificación como leída."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            resultado = _controlador().marcar_notificacion_leida(
                usuario_orm=request.user,
                notificacion_id=request.data.get("notificacion_id"),
                trueque_id=request.data.get("trueque_id"),
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CrearResenaRouter(APIView):
    """POST /resenas/ — Crear reseña de trueque simple."""
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
            resultado = _controlador().registrar_resena(request.user, req_data)
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

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comunidad.controladores.hu_matchmaking_controller import MatchmakingController
from comunidad.dto.request_models import MatchmakingRequest
from comunidad.serializers import MatchEnriquecidoSerializer
from comunidad.services import MatchmakingService
from comunidad.repositorios_implementacion import PublicacionRepository
from comunidad.utils import CsrfExemptSessionAuthentication


class MatchmakingRouter(APIView):
    """Router para GET /matchmaking/ — buscar matches de publicaciones."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            # 1. Construir DTO desde query params
            req_data = MatchmakingRequest(
                publicacion_id=request.query_params.get("publicacion_id"),
                accion=request.query_params.get("accion"),
            )

            # 2. Inyectar dependencias y llamar al controlador
            controlador = MatchmakingController(
                matchmaking_service=MatchmakingService(),
                publicacion_repository=PublicacionRepository(),
            )
            resultado = controlador.obtener_matches(request.user, req_data)

            # 3. Serializar matches si los hay (el serializer es solo mapeo de datos)
            if "matches" in resultado:
                resultado["matches"] = MatchEnriquecidoSerializer(
                    resultado["matches"], many=True
                ).data

            return Response(resultado, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

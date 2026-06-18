"""
Router Sprint 2 HU1 — Impacto Social: Donaciones solidarias de Horas de Vida.
Un Router por endpoint. Traduce HTTP ↔ Controlador.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..controladores.hu_s2_hu1_impacto_social_controller import ImpactoSocialController
from ..services.base import BusinessError
from ..utils import CsrfExemptSessionAuthentication


def _ctrl() -> ImpactoSocialController:
    return ImpactoSocialController()


# ── Solicitudes públicas ───────────────────────────────────────────────────────

class ImpactoSocialSolicitudesRouter(APIView):
    """GET /impacto-social/solicitudes/ — Listar aprobadas.
       POST /impacto-social/solicitudes/ — Crear solicitud."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request):
        try:
            resultado = _ctrl().listar_solicitudes_aprobadas()
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            data = _ctrl().crear_solicitud(request.user, request.data)
            return Response(data, status=status.HTTP_201_CREATED)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MisSolicitudesImpactoSocialRouter(APIView):
    """GET /impacto-social/mis-solicitudes/ — Mis solicitudes."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            resultado = _ctrl().listar_mis_solicitudes(request.user)
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ActivarNecesidadImpactoSocialRouter(APIView):
    """POST /impacto-social/solicitudes/<id>/activar-necesidad/ — Publicar en cartelera."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, solicitud_id: int):
        try:
            resultado = _ctrl().activar_necesidad_vinculada(request.user, solicitud_id)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── Donaciones ─────────────────────────────────────────────────────────────────

class MisDonacionesImpactoSocialRouter(APIView):
    """GET /impacto-social/mis-donaciones/ — Historial de donaciones."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            resultado = _ctrl().listar_mis_donaciones(request.user)
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DonarCausaImpactoSocialRouter(APIView):
    """POST /impacto-social/donar/ — Donar a una causa."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            resultado = _ctrl().donar_a_causa(
                request.user,
                request.data.get("solicitud_id"),
                request.data.get("monto"),
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DonarFondoImpactoSocialRouter(APIView):
    """POST /impacto-social/donar-fondo/ — Donar al fondo comunitario."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            resultado = _ctrl().donar_a_fondo(
                request.user,
                request.data.get("monto"),
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── Admin ──────────────────────────────────────────────────────────────────────

class AdminSolicitudesPendientesImpactoSocialRouter(APIView):
    """GET /admin/impacto-social/solicitudes-pendientes/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            resultado = _ctrl().listar_solicitudes_pendientes(request.user)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminAprobarSolicitudImpactoSocialRouter(APIView):
    """POST /admin/impacto-social/solicitudes/<id>/aprobar/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, solicitud_id: int):
        try:
            data = _ctrl().aprobar_solicitud(request.user, solicitud_id)
            return Response(data, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminRechazarSolicitudImpactoSocialRouter(APIView):
    """POST /admin/impacto-social/solicitudes/<id>/rechazar/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, solicitud_id: int):
        try:
            data = _ctrl().rechazar_solicitud(request.user, solicitud_id)
            return Response(data, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminUsuariosImpactoSocialRouter(APIView):
    """GET /admin/impacto-social/usuarios/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            resultado = _ctrl().listar_usuarios_para_admin(request.user)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminEstadoSocialImpactoSocialRouter(APIView):
    """PATCH /admin/impacto-social/usuarios/<id>/estado-social/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def patch(self, request, usuario_id: int):
        try:
            data = _ctrl().actualizar_estado_social(
                request.user,
                usuario_id,
                request.data.get("estado_social"),
            )
            return Response(data, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminFondoImpactoSocialRouter(APIView):
    """GET /admin/impacto-social/fondo/ — Saldo del fondo comunitario."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            resultado = _ctrl().obtener_saldo_fondo(request.user)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminAsignarFondoImpactoSocialRouter(APIView):
    """POST /admin/impacto-social/fondo/asignar/ — Asignar horas desde el fondo."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            resultado = _ctrl().asignar_desde_fondo(
                request.user,
                request.data.get("usuario_id"),
                request.data.get("monto"),
                request.data.get("solicitud_id"),
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as e:
            return Response({"error": e.message}, status=e.status_code)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

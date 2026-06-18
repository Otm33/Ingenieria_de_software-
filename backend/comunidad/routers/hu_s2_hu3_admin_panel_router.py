"""
Router Sprint 2 HU3 — Panel de Administracion.
Un router (APIView) por endpoint. Todas las rutas requieren autenticacion.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..controladores.hu_s2_hu3_admin_panel_controller import AdminPanelController
from ..utils import CsrfExemptSessionAuthentication


def _controlador():
    return AdminPanelController()


def _respuesta_ok(data):
    return Response(data, status=status.HTTP_200_OK)


def _respuesta_error(error):
    return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)


def _respuesta_error_servidor(error):
    return Response({'error': f'Error interno: {str(error)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── Dashboard ─────────────────────────────────────────────────────────────────

class AdminPanelDashboardRouter(APIView):
    """GET admin/panel/dashboard/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            return _respuesta_ok(_controlador().dashboard(request))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


# ── Usuarios ──────────────────────────────────────────────────────────────────

class AdminPanelUsuariosRouter(APIView):
    """GET admin/panel/usuarios/?q=busqueda"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            return _respuesta_ok(_controlador().listar_usuarios(request))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


class AdminPanelToggleUsuarioRouter(APIView):
    """POST admin/panel/usuarios/<id>/toggle/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, usuario_id):
        try:
            return _respuesta_ok(_controlador().toggle_usuario(request, usuario_id))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


class AdminPanelRolUsuarioRouter(APIView):
    """POST admin/panel/usuarios/<id>/rol/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, usuario_id):
        try:
            return _respuesta_ok(_controlador().cambiar_rol(request, usuario_id))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


class AdminPanelEliminarUsuarioRouter(APIView):
    """DELETE admin/panel/usuarios/<id>/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def delete(self, request, usuario_id):
        try:
            return _respuesta_ok(_controlador().eliminar_usuario(request, usuario_id))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


# ── Publicaciones ─────────────────────────────────────────────────────────────

class AdminPanelPublicacionesRouter(APIView):
    """GET admin/panel/publicaciones/?q=busqueda"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            return _respuesta_ok(_controlador().listar_publicaciones(request))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


class AdminPanelCrearPublicacionRouter(APIView):
    """POST admin/panel/publicaciones/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            return _respuesta_ok(_controlador().crear_publicacion(request))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


class AdminPanelModerarPublicacionRouter(APIView):
    """POST admin/panel/publicaciones/<id>/moderar/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, publicacion_id):
        try:
            return _respuesta_ok(_controlador().moderar_publicacion(request, publicacion_id))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


class AdminPanelEliminarPublicacionRouter(APIView):
    """DELETE admin/panel/publicaciones/<id>/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def delete(self, request, publicacion_id):
        try:
            return _respuesta_ok(_controlador().eliminar_publicacion(request, publicacion_id))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


# ── Trueques ──────────────────────────────────────────────────────────────────

class AdminPanelTruequesRouter(APIView):
    """GET admin/panel/trueques/?q=busqueda"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            return _respuesta_ok(_controlador().listar_trueques(request))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


class AdminPanelEstadoTruequeRouter(APIView):
    """POST admin/panel/trueques/<id>/estado/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, trueque_id):
        try:
            return _respuesta_ok(_controlador().actualizar_estado_trueque(request, trueque_id))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


class AdminPanelEliminarTruequeRouter(APIView):
    """DELETE admin/panel/trueques/<id>/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def delete(self, request, trueque_id):
        try:
            return _respuesta_ok(_controlador().eliminar_trueque(request, trueque_id))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


# ── Trueques Multiples ────────────────────────────────────────────────────────

class AdminPanelTruequesMultiplesRouter(APIView):
    """GET admin/panel/trueques-multiples/?q=busqueda"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            return _respuesta_ok(_controlador().listar_trueques_multiples(request))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


class AdminPanelEstadoTruequeMultipleRouter(APIView):
    """POST admin/panel/trueques-multiples/<id>/estado/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, trueque_id):
        try:
            return _respuesta_ok(_controlador().actualizar_estado_trueque_multiple(request, trueque_id))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


class AdminPanelEliminarTruequeMultipleRouter(APIView):
    """DELETE admin/panel/trueques-multiples/<id>/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def delete(self, request, trueque_id):
        try:
            return _respuesta_ok(_controlador().eliminar_trueque_multiple(request, trueque_id))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


# ── Resenas ───────────────────────────────────────────────────────────────────

class AdminPanelResenasRouter(APIView):
    """GET admin/panel/resenas/?q=busqueda"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            return _respuesta_ok(_controlador().listar_resenas(request))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


class AdminPanelEliminarResenaRouter(APIView):
    """DELETE admin/panel/resenas/<id>/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def delete(self, request, resena_id):
        try:
            return _respuesta_ok(_controlador().eliminar_resena(request, resena_id))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


# ── Resenas Multiples ─────────────────────────────────────────────────────────

class AdminPanelResenasMultiplesRouter(APIView):
    """GET admin/panel/resenas-multiples/?q=busqueda"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            return _respuesta_ok(_controlador().listar_resenas_multiples(request))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


class AdminPanelEliminarResenaMultipleRouter(APIView):
    """DELETE admin/panel/resenas-multiples/<id>/"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def delete(self, request, resena_id):
        try:
            return _respuesta_ok(_controlador().eliminar_resena_multiple(request, resena_id))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)


# ── Saldos Comerciales ────────────────────────────────────────────────────────

class AdminPanelSaldosRouter(APIView):
    """GET admin/panel/saldos/?q=busqueda"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            return _respuesta_ok(_controlador().listar_saldos(request))
        except ValueError as e:
            return _respuesta_error(e)
        except Exception as e:
            return _respuesta_error_servidor(e)

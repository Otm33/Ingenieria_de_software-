"""
Utilidades compartidas por la capa de routers (presentación).

Se extrajeron de views.py para romper la dependencia de los routers
hacia ese archivo legacy y permitir eliminarlo.
"""
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """Autenticación de sesión sin verificación CSRF (usado en endpoints de API)."""

    def enforce_csrf(self, request):
        return


def manejar_error(error):
    """Convierte un BusinessError en una respuesta HTTP de error."""
    return Response({"error": error.message}, status=error.status_code)

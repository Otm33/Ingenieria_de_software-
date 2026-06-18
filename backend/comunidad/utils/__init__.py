"""
Paquete de utilidades compartidas de la capa de presentación.
Re-exporta las utilidades del módulo plano utils.py para mantener
compatibilidad con los imports existentes.
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

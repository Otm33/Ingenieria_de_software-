from django.contrib.auth import authenticate, login, logout
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from comunidad.controladores.hu_autenticacion_controller import AutenticacionController
from comunidad.dto.request_models import LoginRequest
from comunidad.utils import CsrfExemptSessionAuthentication


class SesionRouter(APIView):
    """Router para GET /sesion/ — estado de sesión actual."""
    permission_classes = [AllowAny]

    def get(self, request):
        controlador = AutenticacionController()
        
        # Asegurar que el usuario admin tenga permisos
        if request.user.is_authenticated and request.user.username == 'admin':
            request.user.is_staff = True
            request.user.is_superuser = True
            request.user.save()
        
        resultado = controlador.obtener_sesion(
            usuario_orm=request.user if request.user.is_authenticated else None,
            autenticado=request.user.is_authenticated,
        )
        return Response(resultado, status=status.HTTP_200_OK)


class LoginRouter(APIView):
    """Router para POST /login/ — iniciar sesión."""
    permission_classes = [AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            # 1. Construir DTO
            req_data = LoginRequest(
                username=request.data.get("username", ""),
                password=request.data.get("password", ""),
            )

            # 2. Validar DTO en el controlador
            controlador = AutenticacionController()
            controlador.validar_credenciales(req_data)

            # 3. Autenticar con Django (requiere el objeto request de Django)
            usuario = authenticate(
                request, username=req_data.username, password=req_data.password
            )
            if usuario is None:
                return Response(
                    {"error": "Credenciales inválidas."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # 4. Dar permisos de admin automáticamente al usuario admin
            if usuario.username == 'admin':
                usuario.is_staff = True
                usuario.is_superuser = True
                usuario.save()

            # 5. Crear sesión Django
            login(request, usuario)

            # 5. Construir respuesta usando el controlador
            return Response(
                {
                    "autenticado": True,
                    "usuario": controlador.construir_respuesta_usuario(usuario),
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LogoutRouter(APIView):
    """Router para POST /logout/ — cerrar sesión."""
    permission_classes = [AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        logout(request)
        return Response({"autenticado": False}, status=status.HTTP_200_OK)

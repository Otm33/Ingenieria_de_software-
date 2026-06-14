from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from comunidad.controladores.hu_registro_controller import RegistroUsuarioController
from comunidad.dto.request_models import RegistroUsuarioRequest
from comunidad.repositorios_implementacion import UsuarioRepository
from comunidad.utils import CsrfExemptSessionAuthentication


class RegistroRouter(APIView):
    """
    Router exclusivo para la Historia de Usuario de Registro.
    Recibe la petición web, crea el DTO y llama al Controlador.
    """
    permission_classes = []  # Configurar permisos según necesidad
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            # Construir DTO desde la petición
            req_data = RegistroUsuarioRequest(
                username=request.data.get("username", ""),
                email=request.data.get("email", ""),
                password=request.data.get("password", ""),
                nombre_real=request.data.get("nombre_real", ""),
                es_comercio=request.data.get("es_comercio", False)
            )

            # Inyectar dependencias (Repositorio concreto)
            repo = UsuarioRepository()
            controlador = RegistroUsuarioController(repo)

            # Ejecutar lógica de negocio
            resultado = controlador.ejecutar(req_data)

            # Responder al cliente
            return Response(resultado, status=status.HTTP_201_CREATED)

        except ValueError as e:
            # Error de validación de negocio
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Error interno
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

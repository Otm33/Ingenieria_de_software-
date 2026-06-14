from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from comunidad.controladores.hu_crear_publicacion_controller import CrearPublicacionController
from comunidad.dto.request_models import CrearPublicacionRequest
from comunidad.repositorios_implementacion import PublicacionRepository, UsuarioRepository
from comunidad.views import CsrfExemptSessionAuthentication

class CrearPublicacionRouter(APIView):
    """
    Router exclusivo para la Historia de Usuario de Crear Publicación.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        try:
            # Construir DTO desde la petición
            req_data = CrearPublicacionRequest(
                tipo=request.data.get("tipo", ""),
                titulo=request.data.get("titulo", ""),
                descripcion=request.data.get("descripcion", ""),
                categoria=request.data.get("categoria", ""),
                urgencia=request.data.get("urgencia", "NORMAL")
            )

            # Inyectar dependencias (Repositorios concretos)
            pub_repo = PublicacionRepository()
            usu_repo = UsuarioRepository()
            controlador = CrearPublicacionController(pub_repo, usu_repo)

            # Obtener ID del usuario autenticado (desde el middleware de auth)
            usuario_id = request.user.id

            # Ejecutar lógica de negocio
            resultado = controlador.ejecutar(usuario_id, req_data)

            # Responder al cliente
            return Response(resultado, status=status.HTTP_201_CREATED)

        except ValueError as e:
            # Error de validación de negocio
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Error interno
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status

from .serializers import (
    ImportarMiembroComunidadSerializer,
    VerificarAutorizacionSerializer,  
)


class ImportarMiembrosView(APIView):
    """
    POST /api/comunidad/miembros/importar/
    Recibe un CSV con columnas: nombre, email
    """
    parser_classes = [MultiPartParser]
    
    def post(self, request):
        serializer = ImportarMiembroComunidadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resultado = serializer.save()
        return Response(resultado, status=status.HTTP_201_CREATED)
    
class VerificarAutorizacionView(APIView):
    """
    POST /api/comunidad/auth/verificar/
    Body: { "correo": "oscar@example.com" }
    """
    def post(self, request):
        serializer = VerificarAutorizacionSerializer(data=request.data)
        if serializer.is_valid():
            return Response(
                serializer.to_representation(None),
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_403_FORBIDDEN
        )
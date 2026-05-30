from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout

from .serializers import PublicacionSerializer, UsuarioSerializer
from .services import (
    BusinessError,
    CarteleraService,
    CargaUsuariosService,
    ComercioService,
    MatchmakingService,
    RegistroUsuarioService,
    ResenaService,
    TruequeService,
)


def manejar_error(error):
    return Response({"error": error.message}, status=error.status_code)


class CargarUsuariosCSVView(APIView):
    permission_classes = [AllowAny]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or CargaUsuariosService()

    def post(self, request, format=None):
        archivo = request.FILES.get("archivo_csv") or request.FILES.get("archivo")

        try:
            resultado = self.servicio.cargar_desde_archivo(archivo)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as error:
            return manejar_error(error)
        except Exception as error:
            return Response(
                {"error": f"Error interno al procesar el archivo: {str(error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RegistroUsuarioView(APIView):
    permission_classes = [AllowAny]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or RegistroUsuarioService()

    def post(self, request):
        try:
            usuario = self.servicio.registrar_usuario(request.data)
            return Response(UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED)
        except BusinessError as error:
            return manejar_error(error)


class SesionActualView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # CAMBIO AUTH: permite que Vue sepa si hay sesion activa al entrar en /.
        if not request.user.is_authenticated:
            return Response({"autenticado": False}, status=status.HTTP_200_OK)

        return Response(
            {"autenticado": True, "usuario": UsuarioSerializer(request.user).data},
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # CAMBIO AUTH: autentica contra la BD Django y crea sesion para el frontend.
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Usuario y contrasena son obligatorios."}, status=status.HTTP_400_BAD_REQUEST)

        usuario = authenticate(request, username=username, password=password)
        if usuario is None:
            return Response({"error": "Credenciales invalidas."}, status=status.HTTP_401_UNAUTHORIZED)

        login(request, usuario)
        return Response({"autenticado": True, "usuario": UsuarioSerializer(usuario).data}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # CAMBIO AUTH: cierra la sesion para volver a la pantalla de inicio.
        logout(request)
        return Response({"autenticado": False}, status=status.HTTP_200_OK)


class CarteleraFeedView(generics.ListAPIView):
    serializer_class = PublicacionSerializer

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or CarteleraService()

    def get_queryset(self):
        return self.servicio.obtener_publicaciones(
            categoria=self.request.query_params.get("categoria"),
            urgencia=self.request.query_params.get("urgencia"),
        )


class FinalizarTruequeView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or TruequeService()

    def post(self, request, trueque_id):
        try:
            mensaje = self.servicio.finalizar_trueque(request.user, trueque_id)
            return Response({"message": mensaje})
        except BusinessError as error:
            return manejar_error(error)


class RegistrarResenaView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ResenaService()

    def post(self, request):
        try:
            mensaje = self.servicio.registrar_resena(request.user, request.data)
            return Response({"message": mensaje})
        except BusinessError as error:
            return manejar_error(error)


class EmitirVueltoComercialView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ComercioService()

    def post(self, request):
        try:
            mensaje = self.servicio.emitir_vuelto(request.user, request.data)
            return Response({"message": mensaje})
        except BusinessError as error:
            return manejar_error(error)


class MatchmakingView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or MatchmakingService()

    def get(self, request):
        matches = self.servicio.obtener_matches(request.user)
        serializer = UsuarioSerializer(matches, many=True)
        return Response(
            {"matches": serializer.data, "mensaje": "Se encontraron coincidencias (Match)."},
            status=status.HTTP_200_OK,
        )


class CrearPropuestaView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or TruequeService()

    def post(self, request):
        try:
            propuesta = self.servicio.crear_propuesta(request.user, request.data.get("receptor_id"))
            return Response(
                {"message": "Propuesta enviada con exito.", "propuesta_id": propuesta.id},
                status=status.HTTP_201_CREATED,
            )
        except BusinessError as error:
            return manejar_error(error)


class ResponderPropuestaView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or TruequeService()

    def post(self, request, trueque_id):
        try:
            mensaje = self.servicio.responder_propuesta(
                request.user,
                trueque_id,
                request.data.get("accion"),
            )
            return Response({"message": mensaje})
        except BusinessError as error:
            return manejar_error(error)


class CatalogoComerciosView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UsuarioSerializer

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ComercioService()

    def get_queryset(self):
        return self.servicio.listar_comercios()


class PagarConSaldoView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ComercioService()

    def post(self, request):
        try:
            mensaje = self.servicio.pagar_con_saldo(request.user, request.data)
            return Response({"message": mensaje})
        except BusinessError as error:
            return manejar_error(error)

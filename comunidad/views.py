from rest_framework import generics, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError

from .models import Publicacion, SaldoComercial, Usuario
from .repositories import AcuerdoTruequeRepository, AcuerdoTruequeMultipleRepository, PublicacionRepository, ResenaRepository, UsuarioRepository
from .serializers import (
    AcuerdoTruequeSerializer,
    AcuerdoTruequeMultipleSerializer,
    MatchEnriquecidoSerializer,
    NotificacionSerializer,
    PublicacionSerializer,
    ResenaSerializer,
    ResenaMultipleSerializer,
    SaldoComercialSerializer,
    UsuarioSerializer,
)
from .services import (
    BusinessError,
    CarteleraService,
    CargaUsuariosService,
    ComercioService,
    MatchmakingService,
    NotificacionService,
    PublicacionService,
    RegistroUsuarioService,
    ResenaService,
    TruequeMultipleService,
    TruequeService,
)


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return


def manejar_error(error):
    return Response({"error": error.message}, status=error.status_code)


def es_miembro_activo(usuario):
    nombre = (usuario.nombre_real or "").strip()
    return bool(nombre and Publicacion.objects.filter(usuario=usuario).exists())


class CargarUsuariosCSVView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication]

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


class ValidarEmailRegistroView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or RegistroUsuarioService()

    def post(self, request):
        try:
            self.servicio.validar_email(request.data)
            return Response({"autorizado": True}, status=status.HTTP_200_OK)
        except BusinessError as error:
            return manejar_error(error)


class SesionActualView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # CAMBIO AUTH: permite que Vue sepa si hay sesion activa al entrar en /.
        if not request.user.is_authenticated:
            return Response({"autenticado": False}, status=status.HTTP_200_OK)

        # Asegurar que el usuario admin tenga permisos
        if request.user.username == 'admin':
            request.user.is_staff = True
            request.user.is_superuser = True
            request.user.save()

        return Response(
            {"autenticado": True, "usuario": UsuarioSerializer(request.user).data},
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request):
        # CAMBIO AUTH: autentica contra la BD Django y crea sesion para el frontend.
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Usuario y contrasena son obligatorios."}, status=status.HTTP_400_BAD_REQUEST)

        usuario = authenticate(request, username=username, password=password)
        if usuario is None:
            return Response({"error": "Credenciales invalidas."}, status=status.HTTP_401_UNAUTHORIZED)

        # Dar permisos de admin automáticamente al usuario admin
        if usuario.username == 'admin':
            usuario.is_staff = True
            usuario.is_superuser = True
            usuario.save()

        login(request, usuario)
        return Response({"autenticado": True, "usuario": UsuarioSerializer(usuario).data}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication]

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
        urgencias_raw = self.request.query_params.getlist("urgencia")
        urgencias_validas = {"ALTA", "CRITICA"}
        urgencias = [u for u in urgencias_raw if u in urgencias_validas] or None

        return self.servicio.obtener_publicaciones(
            categoria=self.request.query_params.get("categoria"),
            urgencias=urgencias,
        )


class CrearPublicacionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or PublicacionService()

    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"CrearPublicacionView.post llamado para usuario {request.user.id}")
        try:
            publicacion = self.servicio.crear_publicacion(request.user, request.data)
            logger.warning(f"Publicación creada en vista: ID={publicacion.id}")
            return Response(PublicacionSerializer(publicacion).data, status=status.HTTP_201_CREATED)
        except BusinessError as error:
            return manejar_error(error)
        except ValidationError as error:
            mensaje = "; ".join(error.messages) if hasattr(error, "messages") else str(error)
            return Response({"error": mensaje}, status=status.HTTP_400_BAD_REQUEST)


class ActualizarPublicacionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or PublicacionService()

    def patch(self, request, publicacion_id):
        esta_activa = request.data.get("esta_activa")
        if esta_activa is None or not isinstance(esta_activa, bool):
            return Response(
                {"error": "El campo 'esta_activa' es obligatorio y debe ser booleano."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            publicacion = self.servicio.actualizar_estado_publicacion(
                request.user,
                publicacion_id,
                esta_activa,
            )
            return Response(PublicacionSerializer(publicacion).data, status=status.HTTP_200_OK)
        except BusinessError as error:
            return manejar_error(error)
        except ValidationError as error:
            mensaje = "; ".join(error.messages) if hasattr(error, "messages") else str(error)
            return Response({"error": mensaje}, status=status.HTTP_400_BAD_REQUEST)


class FinalizarTruequeView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or TruequeService()

    def post(self, request, trueque_id):
        try:
            resultado = self.servicio.finalizar_trueque(request.user, trueque_id)
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as error:
            return manejar_error(error)


class ValidarCodigoView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or TruequeService()

    def post(self, request, trueque_id):
        try:
            codigo = request.data.get("codigo")
            if not codigo:
                return Response(
                    {"error": "Falta el código de validación"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            mensaje = self.servicio.validar_codigo(request.user, trueque_id, codigo)
            return Response({"message": mensaje}, status=status.HTTP_200_OK)
        except BusinessError as error:
            return manejar_error(error)


class MisTruequesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            trueques = AcuerdoTruequeRepository().listar_por_usuario(request.user)
            serializer = AcuerdoTruequeSerializer(
                trueques,
                many=True,
                context={"request": request},
            )
            return Response({
                "trueques": serializer.data,
                "cantidad": len(serializer.data),
            }, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(
                {"error": f"Error al obtener mis trueques: {str(error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CrearResenaView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ResenaService()

    def post(self, request):
        try:
            mensaje = self.servicio.registrar_resena(request.user, request.data)
            return Response({"message": mensaje})
        except BusinessError as error:
            return manejar_error(error)


class MiPerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            usuario_data = UsuarioSerializer(request.user).data
            return Response(usuario_data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(
                {"error": f"Error al obtener perfil: {str(error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PerfilOtroUsuarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            usuario = UsuarioRepository().obtener_por_id(user_id)
            serializer = UsuarioSerializer(usuario)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(
                {"error": f"Error al obtener perfil de usuario: {str(error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MisPublicacionesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            publicaciones = PublicacionRepository().listar_por_usuario(request.user)
            serializer = PublicacionSerializer(publicaciones, many=True)
            return Response({
                "publicaciones": serializer.data,
                "cantidad": len(serializer.data),
            }, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(
                {"error": f"Error al obtener mis publicaciones: {str(error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DirectorioComunidadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        publicacion_repository = PublicacionRepository()
        miembros = Usuario.objects.filter(
            is_active=True,
            is_staff=False,
            is_superuser=False,
        ).order_by("nombre_real", "username")

        directorio = []
        for miembro in miembros:
            publicaciones = publicacion_repository.listar_por_usuario(miembro)
            talentos_activos = [
                publicacion for publicacion in publicaciones
                if publicacion.tipo == "TALENTO" and publicacion.esta_activa
            ]

            directorio.append({
                "id": miembro.id,
                "nombre_real": miembro.nombre_real,
                "username": miembro.username,
                "promedio_estrellas": miembro.promedio_estrellas,
                "talentos_principales": [publicacion.titulo for publicacion in talentos_activos[:3]],
                "cantidad_talentos": len(talentos_activos),
                "es_miembro_activo": es_miembro_activo(miembro),
            })

        return Response({
            "miembros": directorio,
            "cantidad": len(directorio),
        }, status=status.HTTP_200_OK)


class NotificacionesView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or NotificacionService()

    def get(self, request):
        """Obtiene las notificaciones del usuario (pendientes por defecto)."""
        try:
            incluir_leidas = request.query_params.get('incluir_leidas', '').lower() in (
                '1', 'true', 'yes',
            )
            notificaciones = self.servicio.obtener_notificaciones_usuario(
                request.user,
                incluir_leidas=incluir_leidas,
            )
            notificaciones_data = NotificacionSerializer(
                notificaciones,
                many=True,
                context={"request": request},
            ).data

            return Response({
                "notificaciones": notificaciones_data,
                "cantidad": len(notificaciones_data),
            }, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(
                {"error": f"Error al obtener notificaciones: {str(error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    def post(self, request):
        """Marca notificaciones como leídas (por id o por trueque)."""
        notificacion_id = request.data.get("notificacion_id")
        trueque_id = request.data.get("trueque_id")

        if not notificacion_id and not trueque_id:
            return Response(
                {"error": "Falta notificacion_id o trueque_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if trueque_id:
                cantidad = self.servicio.marcar_notificaciones_trueque_leidas(
                    request.user,
                    trueque_id,
                )
                return Response(
                    {
                        "message": "Notificaciones del trueque marcadas como leídas",
                        "cantidad": cantidad,
                    },
                    status=status.HTTP_200_OK,
                )

            self.servicio.marcar_notificacion_leida(notificacion_id, request.user)
            return Response(
                {"message": "Notificación marcada como leída"},
                status=status.HTTP_200_OK,
            )
        except BusinessError as error:
            return manejar_error(error)
        except Exception as error:
            return Response(
                {"error": f"Error al marcar notificación: {str(error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AceptarPropuestaMultipleView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or TruequeMultipleService()

    def post(self, request, trueque_multiple_id):
        try:
            mensaje = self.servicio.aceptar_propuesta_multiple(request.user, trueque_multiple_id)
            return Response({"message": mensaje}, status=status.HTTP_200_OK)
        except BusinessError as error:
            return manejar_error(error)


class RechazarPropuestaMultipleView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or TruequeMultipleService()

    def post(self, request, trueque_multiple_id):
        try:
            mensaje = self.servicio.rechazar_propuesta_multiple(request.user, trueque_multiple_id)
            return Response({"message": mensaje}, status=status.HTTP_200_OK)
        except BusinessError as error:
            return manejar_error(error)


class ValidarCodigoParMultipleView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or TruequeMultipleService()

    def post(self, request, trueque_multiple_id):
        try:
            codigo = request.data.get("codigo")
            if not codigo:
                return Response(
                    {"error": "Falta el código de validación"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            mensaje = self.servicio.validar_codigo_par(request.user, trueque_multiple_id, codigo)
            return Response({"message": mensaje}, status=status.HTTP_200_OK)
        except BusinessError as error:
            return manejar_error(error)


class FinalizarParMultipleView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or TruequeMultipleService()

    def post(self, request, trueque_multiple_id):
        try:
            mensaje = self.servicio.finalizar_par(request.user, trueque_multiple_id)
            return Response({"message": mensaje}, status=status.HTTP_200_OK)
        except BusinessError as error:
            return manejar_error(error)


class MisTruequesMultipleView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            trueques_multiple = AcuerdoTruequeMultipleRepository().listar_por_usuario(request.user)
            serializer = AcuerdoTruequeMultipleSerializer(
                trueques_multiple,
                many=True,
                context={"request": request},
            )
            return Response({
                "trueques_multiple": serializer.data,
                "cantidad": len(serializer.data),
            }, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(
                {"error": f"Error al obtener trueques múltiples: {str(error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RegistrarResenaMultipleView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        from .services import ResenaMultipleService
        self.servicio = servicio or ResenaMultipleService()

    def post(self, request):
        try:
            mensaje = self.servicio.registrar_resena_multiple(request.user, request.data)
            return Response({"message": mensaje})
        except BusinessError as error:
            return manejar_error(error)


class SetupAdminView(APIView):
    """Vista temporal para configurar permisos de admin."""
    permission_classes = [AllowAny]

    def get(self, request, username):
        try:
            usuario = Usuario.objects.get(username=username)
            usuario.is_staff = True
            usuario.is_superuser = True
            usuario.save()
            return Response({
                "message": f"Usuario '{username}' configurado como admin exitosamente",
                "is_staff": usuario.is_staff,
                "is_superuser": usuario.is_superuser,
                "esStaff": usuario.is_staff,
                "esSuperusuario": usuario.is_superuser,
            }, status=status.HTTP_200_OK)
        except Usuario.DoesNotExist:
            return Response(
                {"error": f"El usuario '{username}' no existe"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": f"Error al configurar admin: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
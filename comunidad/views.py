from rest_framework import generics, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError

from .models import Publicacion, Usuario
from .repositories import PublicacionRepository, ResenaRepository, UsuarioRepository
from .serializers import PublicacionSerializer, UsuarioSerializer, ResenaSerializer
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
        return self.servicio.obtener_publicaciones(
            categoria=self.request.query_params.get("categoria"),
            urgencia=self.request.query_params.get("urgencia"),
        )


class CrearPublicacionView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or PublicacionService()

    def post(self, request):
        try:
            publicacion = self.servicio.crear_publicacion(request.user, request.data)
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
        # Verificar si se proporciona un ID de publicación específica
        publicacion_id = request.query_params.get("publicacion_id")
        accion = request.query_params.get("accion")
        
        if accion == "verificar_coincidencia" and publicacion_id:
            # Verificar si el usuario tiene publicaciones con el mismo título
            resultado = self.servicio.verificar_coincidencia_por_titulo(request.user, publicacion_id)
            return Response(resultado, status=status.HTTP_200_OK)
        
        if publicacion_id:
            # Buscar matches basados en la publicación específica
            matches = self.servicio.obtener_matches_por_publicacion(request.user, publicacion_id)
            mensaje = f"Se encontraron coincidencias para la publicación seleccionada."
        else:
            # Buscar matches basados en todas las publicaciones del usuario (comportamiento original)
            matches = self.servicio.obtener_matches(request.user)
            mensaje = "Se encontraron coincidencias (Match)."
        
        serializer = UsuarioSerializer(matches, many=True)
        return Response(
            {"matches": serializer.data, "mensaje": mensaje},
            status=status.HTTP_200_OK,
        )


class CrearPropuestaView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or TruequeService()

    def post(self, request):
        try:
            propuesta = self.servicio.crear_propuesta(
                request.user, 
                request.data.get("receptor_id"),
                request.data.get("publicacion_emisor_id"),
                request.data.get("publicacion_receptor_id")
            )
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


class VerPerfilUsuarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, usuario_id):
        try:
            usuario_repository = UsuarioRepository()
            publicacion_repository = PublicacionRepository()
            resena_repository = ResenaRepository()

            usuario = usuario_repository.obtener_por_id(usuario_id)
            publicaciones_activas = publicacion_repository.listar_por_usuario(usuario, solo_activas=True)
            publicaciones_data = PublicacionSerializer(publicaciones_activas, many=True).data
            resenas_recibidas = resena_repository.listar_por_calificado(usuario)
            resenas_data = ResenaSerializer(resenas_recibidas, many=True).data

            return Response({
                "usuario": UsuarioSerializer(usuario).data,
                "nombre_real": usuario.nombre_real,
                "promedio_estrellas": usuario.promedio_estrellas,
                "publicaciones": publicaciones_data,
                "resenas": resenas_data,
                "cantidad_publicaciones": len(publicaciones_data),
                "cantidad_resenas": len(resenas_data),
            }, status=status.HTTP_200_OK)

        except Exception as error:
            return Response(
                {"error": f"Error al obtener perfil: {str(error)}"},
                status=status.HTTP_404_NOT_FOUND,
            )


class VerSaldoComercialView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from .repositories import SaldoComercialRepository
            saldo_repository = SaldoComercialRepository()
            
            # Obtener saldo actual del usuario
            saldo_actual = request.user.saldo_comercial
            
            # Obtener movimientos del usuario como cliente
            movimientos_cliente = SaldoComercial.objects.filter(
                cliente=request.user
            ).order_by('-fecha')
            
            # Obtener movimientos del usuario como comercio (si es comercio)
            movimientos_comercio = []
            if request.user.es_comercio:
                movimientos_comercio = SaldoComercial.objects.filter(
                    comercio=request.user
                ).order_by('-fecha')
            
            serializer_cliente = SaldoComercialSerializer(movimientos_cliente, many=True)
            serializer_comercio = SaldoComercialSerializer(movimientos_comercio, many=True)
            
            return Response({
                "saldo_actual": float(saldo_actual),
                "movimientos_como_cliente": serializer_cliente.data,
                "movimientos_como_comercio": serializer_comercio.data,
                "es_comercio": request.user.es_comercio
            }, status=status.HTTP_200_OK)
            
        except Exception as error:
            return Response(
                {"error": f"Error al obtener saldo comercial: {str(error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerMiPerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            from .models import AcuerdoTrueque

            publicacion_repository = PublicacionRepository()
            resena_repository = ResenaRepository()

            publicaciones = publicacion_repository.listar_por_usuario(request.user)
            publicaciones_activas = [publicacion for publicacion in publicaciones if publicacion.esta_activa]
            publicaciones_pausadas = [publicacion for publicacion in publicaciones if not publicacion.esta_activa]

            resenas_recibidas = resena_repository.listar_por_calificado(request.user)
            trueques_enviados = AcuerdoTrueque.objects.filter(emisor=request.user)
            trueques_recibidos = AcuerdoTrueque.objects.filter(receptor=request.user)

            return Response({
                "usuario": UsuarioSerializer(request.user).data,
                "publicaciones": PublicacionSerializer(publicaciones, many=True).data,
                "publicaciones_activas": PublicacionSerializer(publicaciones_activas, many=True).data,
                "publicaciones_pausadas": PublicacionSerializer(publicaciones_pausadas, many=True).data,
                "resenas_recibidas": ResenaSerializer(resenas_recibidas, many=True).data,
                "trueques_enviados_count": trueques_enviados.count(),
                "trueques_recibidos_count": trueques_recibidos.count(),
                "saldo_comercial": float(request.user.saldo_comercial),
                "es_miembro_activo": es_miembro_activo(request.user),
                "cantidad_publicaciones_pausadas": len(publicaciones_pausadas),
            }, status=status.HTTP_200_OK)

        except Exception as error:
            return Response(
                {"error": f"Error al obtener mi perfil: {str(error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MisPublicacionesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            publicacion_repository = PublicacionRepository()
            publicaciones = publicacion_repository.listar_por_usuario(request.user)
            publicaciones_data = PublicacionSerializer(publicaciones, many=True).data

            return Response({
                "publicaciones": publicaciones_data,
                "cantidad": len(publicaciones_data),
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

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or NotificacionService()

    def get(self, request):
        """Obtiene las notificaciones no leídas del usuario."""
        try:
            notificaciones = self.servicio.obtener_notificaciones_usuario(request.user)
            
            # Serializar las notificaciones
            notificaciones_data = []
            for notif in notificaciones:
                notificaciones_data.append({
                    "id": notif.id,
                    "mensaje": notif.mensaje,
                    "remitente_nombre": notif.remitente.nombre_real,
                    "remitente_username": notif.remitente.username,
                    "estado": notif.estado,
                    "creada_el": notif.creada_el.isoformat() if notif.creada_el else None,
                    "trueque_id": notif.trueque.id,
                    "publicacion_titulo": notif.publicacion_original.titulo,
                    "publicacion_tipo": notif.publicacion_original.tipo,
                    "prioridad": notif.prioridad
                })
            
            return Response({
                "notificaciones": notificaciones_data,
                "cantidad": len(notificaciones_data)
            }, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(
                {"error": f"Error al obtener notificaciones: {str(error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    def post(self, request):
        """Marca una notificación como leída."""
        notificacion_id = request.data.get("notificacion_id")
        if not notificacion_id:
            return Response(
                {"error": "Falta notificacion_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            self.servicio.marcar_notificacion_leida(notificacion_id)
            return Response(
                {"message": "Notificación marcada como leída"},
                status=status.HTTP_200_OK,
            )
        except Exception as error:
            return Response(
                {"error": f"Error al marcar notificación: {str(error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

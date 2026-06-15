from rest_framework import generics, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError

from .models import DonacionHoras, Publicacion, SaldoComercial, Usuario
from .serializers import (
    AcuerdoTruequeSerializer,
    ClienteBasicoSerializer,
    DonacionHorasSerializer,
    MatchEnriquecidoSerializer,
    NotificacionSerializer,
    PublicacionSerializer,
    ResenaSerializer,
    SaldoComercialSerializer,
    SolicitudApoyoSocialSerializer,
    UsuarioEstadoSocialSerializer,
    UsuarioSerializer,
)
from .services import (
    BusinessError,
    CarteleraService,
    CargaUsuariosService,
    ComercioService,
    ComunidadService,
    ImpactoSocialService,
    MENSAJE_SOLICITANTE_MARCADO_VULNERABLE,
    MatchmakingService,
    NotificacionService,
    PerfilService,
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
    return ComunidadService.es_miembro_activo(usuario)


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
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or TruequeService()

    def post(self, request, trueque_id):
        try:
            resultado = self.servicio.finalizar_trueque(request.user, trueque_id)
            trueque = self.servicio.obtener_por_participante(trueque_id, request.user)
            return Response({
                "message": resultado.get("mensaje", ""),
                "estado": trueque.estado,
                "emisor_confirmado": trueque.emisor_confirmado,
                "receptor_confirmado": trueque.receptor_confirmado,
                "saldo_transferido": resultado.get("saldo_transferido", False),
                "impacto_horas": resultado.get("impacto_horas", 0),
                "habilitar_resena": resultado.get("habilitar_resena", False),
            })
        except BusinessError as error:
            return manejar_error(error)


class RegistrarResenaView(APIView):
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


class EmitirVueltoComercialView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ComercioService()

    def post(self, request):
        try:
            resultado = self.servicio.emitir_vuelto(request.user, request.data)
            comprobante = SaldoComercialSerializer(resultado["comprobante"]).data
            return Response({
                "message": resultado["mensaje"],
                "comprobante": comprobante,
                "saldo_cliente": float(resultado["saldo_cliente"]),
                "saldo_comercio": float(resultado["saldo_comercio"]),
            })
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
            matches = self.servicio.obtener_matches_por_publicacion(request.user, publicacion_id)
            mensaje = "Se encontraron coincidencias para la publicación seleccionada."
        else:
            matches = self.servicio.obtener_matches(request.user)
            mensaje = "Se encontraron coincidencias (Match)."

        matches_data = MatchEnriquecidoSerializer(matches, many=True).data
        return Response(
            {"matches": matches_data, "mensaje": mensaje, "cantidad": len(matches_data)},
            status=status.HTTP_200_OK,
        )


class CrearPropuestaView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

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


class MisTruequesView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or TruequeService()

    def get(self, request):
        trueques = self.servicio.listar_por_usuario(request.user)
        serializer = AcuerdoTruequeSerializer(
            trueques,
            many=True,
            context={"request": request},
        )
        return Response({
            "trueques": serializer.data,
            "cantidad": len(serializer.data),
        }, status=status.HTTP_200_OK)


class ResponderPropuestaView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

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


class CatalogoClientesView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ComercioService()

    def get(self, request):
        try:
            if not request.user.es_comercio:
                raise BusinessError(
                    "Solo comercios pueden consultar el listado de clientes.",
                    status_code=403,
                )

            termino = request.query_params.get("q")
            clientes = self.servicio.listar_clientes(termino)
            data = ClienteBasicoSerializer(clientes, many=True).data
            return Response(data, status=status.HTTP_200_OK)
        except BusinessError as error:
            return manejar_error(error)


class PagarConSaldoView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ComercioService()

    def post(self, request):
        try:
            resultado = self.servicio.pagar_con_saldo(request.user, request.data)
            comprobante = SaldoComercialSerializer(resultado["comprobante"]).data
            return Response({
                "message": resultado["mensaje"],
                "comprobante": comprobante,
                "saldo_restante": float(resultado["saldo_restante"]),
                "saldo_comercio": float(resultado["saldo_comercio"]),
            })
        except BusinessError as error:
            return manejar_error(error)


class VerPerfilUsuarioView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or PerfilService()

    def get(self, request, usuario_id):
        try:
            usuario, publicaciones_activas, resenas_recibidas = self.servicio.obtener_perfil_publico(usuario_id)
            publicaciones_data = PublicacionSerializer(publicaciones_activas, many=True).data
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
            usuario_actual = Usuario.objects.obtener_por_id(request.user.id)
            saldo_actual = usuario_actual.saldo_comercial
            
            # Obtener movimientos del usuario como cliente
            movimientos_cliente = SaldoComercial.objects.filter(
                cliente=usuario_actual
            ).order_by('-fecha')
            
            # Obtener movimientos del usuario como comercio (si es comercio)
            movimientos_comercio = []
            if usuario_actual.es_comercio:
                movimientos_comercio = SaldoComercial.objects.filter(
                    comercio=usuario_actual
                ).order_by('-fecha')
            
            serializer_cliente = SaldoComercialSerializer(movimientos_cliente, many=True)
            serializer_comercio = SaldoComercialSerializer(movimientos_comercio, many=True)
            
            return Response({
                "saldo_actual": float(saldo_actual),
                "movimientos_como_cliente": serializer_cliente.data,
                "movimientos_como_comercio": serializer_comercio.data,
                "es_comercio": usuario_actual.es_comercio
            }, status=status.HTTP_200_OK)
            
        except Exception as error:
            return Response(
                {"error": f"Error al obtener saldo comercial: {str(error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerMiPerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or PerfilService()

    def get(self, request):
        try:
            datos = self.servicio.obtener_mi_perfil(request.user)
            resenas_data = ResenaSerializer(datos["resenas_recibidas"], many=True).data

            return Response({
                "usuario": UsuarioSerializer(request.user).data,
                "promedio_estrellas": request.user.promedio_estrellas,
                "publicaciones": PublicacionSerializer(datos["publicaciones"], many=True).data,
                "publicaciones_activas": PublicacionSerializer(datos["publicaciones_activas"], many=True).data,
                "publicaciones_pausadas": PublicacionSerializer(datos["publicaciones_pausadas"], many=True).data,
                "resenas_recibidas": resenas_data,
                "cantidad_resenas": len(resenas_data),
                "trueques_enviados_count": datos["trueques_enviados_count"],
                "trueques_recibidos_count": datos["trueques_recibidos_count"],
                "saldo_comercial": float(request.user.saldo_comercial),
                "es_miembro_activo": es_miembro_activo(request.user),
                "cantidad_publicaciones_pausadas": len(datos["publicaciones_pausadas"]),
            }, status=status.HTTP_200_OK)

        except Exception as error:
            return Response(
                {"error": f"Error al obtener mi perfil: {str(error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MisPublicacionesView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or PerfilService()

    def get(self, request):
        try:
            publicaciones = self.servicio.listar_mis_publicaciones(request.user)
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

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ComunidadService()

    def get(self, request):
        directorio = self.servicio.obtener_directorio()

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


class ImpactoSocialSolicitudesView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ImpactoSocialService()

    def get(self, request):
        solicitudes = self.servicio.listar_solicitudes_aprobadas()
        return Response({
            "solicitudes": solicitudes,
            "cantidad": len(solicitudes),
        }, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            solicitud = self.servicio.crear_solicitud(request.user, request.data)
            return Response(
                SolicitudApoyoSocialSerializer(solicitud).data,
                status=status.HTTP_201_CREATED,
            )
        except BusinessError as error:
            return manejar_error(error)


class MisSolicitudesImpactoSocialView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ImpactoSocialService()

    def get(self, request):
        solicitudes = self.servicio.listar_mis_solicitudes(request.user)
        data = SolicitudApoyoSocialSerializer(solicitudes, many=True).data
        return Response({
            "solicitudes": data,
            "cantidad": len(data),
        }, status=status.HTTP_200_OK)


class ActivarNecesidadImpactoSocialView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ImpactoSocialService()

    def post(self, request, solicitud_id):
        try:
            solicitud = self.servicio.activar_necesidad_vinculada(request.user, solicitud_id)
            return Response({
                "solicitud": SolicitudApoyoSocialSerializer(solicitud).data,
                "publicacion_id": solicitud.publicacion_id,
            }, status=status.HTTP_200_OK)
        except BusinessError as error:
            return manejar_error(error)


class MisDonacionesImpactoSocialView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ImpactoSocialService()

    def get(self, request):
        realizadas = self.servicio.listar_mis_donaciones_realizadas(request.user)
        recibidas = self.servicio.listar_mis_donaciones_recibidas(request.user)
        return Response({
            "realizadas": DonacionHorasSerializer(realizadas, many=True).data,
            "recibidas": DonacionHorasSerializer(recibidas, many=True).data,
            "cantidad_realizadas": len(realizadas),
            "cantidad_recibidas": len(recibidas),
        }, status=status.HTTP_200_OK)


class DonarCausaImpactoSocialView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ImpactoSocialService()

    def post(self, request):
        try:
            resultado = self.servicio.donar_a_causa(
                request.user,
                request.data.get("solicitud_id"),
                request.data.get("monto"),
            )
            donacion = DonacionHoras.objects.get(id=resultado["donacion_id"])
            return Response({
                "message": resultado["mensaje"],
                "comprobante": DonacionHorasSerializer(donacion).data,
                "saldo_restante": resultado["saldo_restante"],
                "monto": resultado["monto"],
                "receptor_id": resultado["receptor_id"],
                "receptor_nombre": resultado["receptor_nombre"],
            }, status=status.HTTP_200_OK)
        except BusinessError as error:
            return manejar_error(error)


class DonarFondoImpactoSocialView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ImpactoSocialService()

    def post(self, request):
        try:
            resultado = self.servicio.donar_a_fondo(
                request.user,
                request.data.get("monto"),
            )
            donacion = DonacionHoras.objects.get(id=resultado["donacion_id"])
            fondo = self.servicio.obtener_saldo_fondo()
            return Response({
                "message": resultado["mensaje"],
                "comprobante": DonacionHorasSerializer(donacion).data,
                "saldo_restante": resultado["saldo_restante"],
                "saldo_fondo": fondo["saldo"],
                "monto": resultado["monto"],
            }, status=status.HTTP_200_OK)
        except BusinessError as error:
            return manejar_error(error)


class AdminSolicitudesPendientesImpactoSocialView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ImpactoSocialService()

    def get(self, request):
        try:
            solicitudes = self.servicio.listar_solicitudes_pendientes(request.user)
            data = SolicitudApoyoSocialSerializer(solicitudes, many=True).data
            return Response({
                "solicitudes": data,
                "cantidad": len(data),
            }, status=status.HTTP_200_OK)
        except BusinessError as error:
            return manejar_error(error)


class AdminAprobarSolicitudImpactoSocialView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ImpactoSocialService()

    def post(self, request, solicitud_id):
        try:
            solicitud = self.servicio.aprobar_solicitud(request.user, solicitud_id)
            data = SolicitudApoyoSocialSerializer(solicitud).data
            if getattr(solicitud, "solicitante_marcado_vulnerable", False):
                data["mensaje"] = MENSAJE_SOLICITANTE_MARCADO_VULNERABLE
            else:
                data["mensaje"] = "Solicitud aprobada correctamente."
            return Response(data, status=status.HTTP_200_OK)
        except BusinessError as error:
            return manejar_error(error)


class AdminRechazarSolicitudImpactoSocialView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ImpactoSocialService()

    def post(self, request, solicitud_id):
        try:
            solicitud = self.servicio.rechazar_solicitud(request.user, solicitud_id)
            return Response(
                SolicitudApoyoSocialSerializer(solicitud).data,
                status=status.HTTP_200_OK,
            )
        except BusinessError as error:
            return manejar_error(error)


class AdminUsuariosImpactoSocialView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ImpactoSocialService()

    def get(self, request):
        try:
            usuarios = self.servicio.listar_usuarios_para_admin(request.user)
            data = UsuarioEstadoSocialSerializer(usuarios, many=True).data
            return Response({
                "usuarios": data,
                "cantidad": len(data),
            }, status=status.HTTP_200_OK)
        except BusinessError as error:
            return manejar_error(error)


class AdminEstadoSocialImpactoSocialView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ImpactoSocialService()

    def patch(self, request, usuario_id):
        try:
            usuario = self.servicio.actualizar_estado_social(
                request.user,
                usuario_id,
                request.data.get("estado_social"),
            )
            return Response(
                UsuarioEstadoSocialSerializer(usuario).data,
                status=status.HTTP_200_OK,
            )
        except BusinessError as error:
            return manejar_error(error)


class AdminFondoImpactoSocialView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ImpactoSocialService()

    def get(self, request):
        try:
            fondo = self.servicio.obtener_saldo_fondo(request.user)
            return Response(fondo, status=status.HTTP_200_OK)
        except BusinessError as error:
            return manejar_error(error)


class AdminAsignarFondoImpactoSocialView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def __init__(self, *args, servicio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.servicio = servicio or ImpactoSocialService()

    def post(self, request):
        try:
            resultado = self.servicio.asignar_desde_fondo(
                request.user,
                request.data.get("usuario_id"),
                request.data.get("monto"),
                request.data.get("solicitud_id"),
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except BusinessError as error:
            return manejar_error(error)

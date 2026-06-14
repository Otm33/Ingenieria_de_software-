from django.urls import path

# HU Autenticación
from .routers.autenticacion_router import SesionRouter, LoginRouter, LogoutRouter

# HU Registro
from .routers.registro_router import RegistroRouter

# Administración y soporte
from .routers.admin_router import SetupAdminRouter, CargarUsuariosCSVRouter, ValidarEmailRegistroRouter

# HU Publicaciones
from .routers.publicacion_router import CrearPublicacionRouter
from .routers.gestion_publicacion_router import GestionPublicacionRouter, MisPublicacionesRouter, CarteleraRouter

# HU Perfil
from .routers.perfil_router import MiPerfilRouter, PerfilOtroUsuarioRouter, ComunidadRouter

# HU Matchmaking
from .routers.matchmaking_router import MatchmakingRouter

# HU Proponer Trueque
from .routers.proponer_trueque_router import CrearPropuestaRouter, ResponderPropuestaRouter, MisTruequesRouter

# HU Finalizar Trueque
from .routers.finalizar_trueque_router import FinalizarTruequeRouter, ValidarCodigoRouter

# HU Reseña
from .routers.resena_router import CrearResenaRouter, CrearResenaMultipleRouter

# HU Saldo Comercial
from .routers.saldo_comercial_router import EmitirVueltoRouter, PagarConSaldoRouter, MiSaldoComercialRouter, ComerciosRouter, ClientesRouter

# HU Notificaciones
from .routers.notificacion_router import NotificacionRouter, MarcarLeidaRouter

# HU Trueque Múltiple
from .routers.trueque_multiple_router import (
    AceptarTruequeMultipleRouter,
    RechazarTruequeMultipleRouter,
    ValidarCodigoTruequeMultipleRouter,
    FinalizarTruequeMultipleRouter,
    MisTruequesMultiplesRouter,
)


urlpatterns = [
    # Administración temporal
    path('setup-admin/<str:username>/', SetupAdminRouter.as_view(), name='setup_admin_temp'),

    # Autenticación
    path('sesion/', SesionRouter.as_view(), name='sesion_actual'),
    path('login/', LoginRouter.as_view(), name='login'),
    path('logout/', LogoutRouter.as_view(), name='logout'),

    # Registro
    path('registro/', RegistroRouter.as_view(), name='registro'),
    path('registro/validar-email/', ValidarEmailRegistroRouter.as_view(), name='validar_email_registro'),
    path('cargar-csv/', CargarUsuariosCSVRouter.as_view(), name='cargar_csv'),

    # Perfil / Comunidad
    path('comunidad/', ComunidadRouter.as_view(), name='directorio_comunidad'),
    path('perfil/<int:user_id>/', PerfilOtroUsuarioRouter.as_view(), name='ver_perfil_usuario'),
    path('mi-perfil/', MiPerfilRouter.as_view(), name='ver_mi_perfil'),

    # Publicaciones
    path('cartelera/', CarteleraRouter.as_view(), name='cartelera'),
    path('publicaciones/', CrearPublicacionRouter.as_view(), name='crear_publicacion'),
    path('publicaciones/<int:pk>/', GestionPublicacionRouter.as_view(), name='actualizar_publicacion'),
    path('mis-publicaciones/', MisPublicacionesRouter.as_view(), name='mis_publicaciones'),

    # HU4: Match y Propuestas
    path('matchmaking/', MatchmakingRouter.as_view(), name='matchmaking'),
    path('trueques/propuestas/crear/', CrearPropuestaRouter.as_view(), name='crear_propuesta'),
    path('trueques/<int:trueque_id>/responder/', ResponderPropuestaRouter.as_view(), name='responder_propuesta'),

    # HU4: Finalizar y Reseñas
    path('trueques/<int:trueque_id>/finalizar/', FinalizarTruequeRouter.as_view(), name='finalizar_trueque'),
    path('trueques/<int:trueque_id>/validar-codigo/', ValidarCodigoRouter.as_view(), name='validar_codigo'),
    path('mis-trueques/', MisTruequesRouter.as_view(), name='mis_trueques'),
    path('resenas/', CrearResenaRouter.as_view(), name='registrar_resena'),

    # Notificaciones
    path('notificaciones/', NotificacionRouter.as_view(), name='notificaciones'),
    path('notificaciones/marcar-leida/', MarcarLeidaRouter.as_view(), name='marcar_leida'),

    # Saldos comerciales
    path('comercio/emitir-vuelto/', EmitirVueltoRouter.as_view(), name='emitir_vuelto'),
    path('comercios/', ComerciosRouter.as_view(), name='catalogo_comercios'),
    path('clientes/', ClientesRouter.as_view(), name='catalogo_clientes'),
    path('comercio/pagar/', PagarConSaldoRouter.as_view(), name='pagar_con_saldo'),
    path('mi-saldo-comercial/', MiSaldoComercialRouter.as_view(), name='ver_saldo_comercial'),

    # Trueques múltiples
    path('mis-trueques-multiples/', MisTruequesMultiplesRouter.as_view(), name='mis_trueques_multiples'),
    path('trueques-multiples/<int:trueque_multiple_id>/aceptar/', AceptarTruequeMultipleRouter.as_view(), name='aceptar_propuesta_multiple'),
    path('trueques-multiples/<int:trueque_multiple_id>/rechazar/', RechazarTruequeMultipleRouter.as_view(), name='rechazar_propuesta_multiple'),
    path('trueques-multiples/<int:trueque_multiple_id>/validar-codigo/', ValidarCodigoTruequeMultipleRouter.as_view(), name='validar_codigo_par_multiple'),
    path('trueques-multiples/<int:trueque_multiple_id>/finalizar-par/', FinalizarTruequeMultipleRouter.as_view(), name='finalizar_par_multiple'),
    path('resenas-multiples/', CrearResenaMultipleRouter.as_view(), name='registrar_resena_multiple'),
]

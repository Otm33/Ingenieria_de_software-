from django.urls import path
from .views import (
    CargarUsuariosCSVView,
    RegistroUsuarioView,
    ValidarEmailRegistroView,
    SesionActualView,
    LoginView,
    LogoutView,
    CarteleraFeedView,
    CrearPublicacionView,
    ActualizarPublicacionView,
    FinalizarTruequeView,
    ValidarCodigoView,
    MisTruequesView,
    RegistrarResenaView,
    EmitirVueltoComercialView,
    MatchmakingView,
    CrearPropuestaView,
    ResponderPropuestaView,
    CatalogoComerciosView,
    PagarConSaldoView,
    VerPerfilUsuarioView,
    VerSaldoComercialView,
    VerMiPerfilView,
    MisPublicacionesView,
    DirectorioComunidadView,
    NotificacionesView,
)

# CAMBIO CONTROLADOR: estas rutas son la frontera HTTP que consume la vista Vue.
urlpatterns = [
    path('sesion/', SesionActualView.as_view(), name='sesion_actual'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('cargar-csv/', CargarUsuariosCSVView.as_view(), name='cargar_csv'),
    path('registro/', RegistroUsuarioView.as_view(), name='registro'),
    path('registro/validar-email/', ValidarEmailRegistroView.as_view(), name='validar_email_registro'),
    path('comunidad/', DirectorioComunidadView.as_view(), name='directorio_comunidad'),
    path('cartelera/', CarteleraFeedView.as_view(), name='cartelera'),
    path('publicaciones/', CrearPublicacionView.as_view(), name='crear_publicacion'),
    path('publicaciones/<int:publicacion_id>/', ActualizarPublicacionView.as_view(), name='actualizar_publicacion'),
    
    # HU4: Match y Propuestas
    path('matchmaking/', MatchmakingView.as_view(), name='matchmaking'),
    path('trueques/propuestas/crear/', CrearPropuestaView.as_view(), name='crear_propuesta'),
    path('trueques/<int:trueque_id>/responder/', ResponderPropuestaView.as_view(), name='responder_propuesta'),
    
    # HU4: Finalizar y Reseñas
    path('trueques/<int:trueque_id>/finalizar/', FinalizarTruequeView.as_view(), name='finalizar_trueque'),
    path('trueques/<int:trueque_id>/validar-codigo/', ValidarCodigoView.as_view(), name='validar_codigo'),
    path('mis-trueques/', MisTruequesView.as_view(), name='mis_trueques'),
    path('resenas/', RegistrarResenaView.as_view(), name='registrar_resena'),
    
    # Perfiles de usuarios
    path('perfil/<int:usuario_id>/', VerPerfilUsuarioView.as_view(), name='ver_perfil_usuario'),
    path('mi-perfil/', VerMiPerfilView.as_view(), name='ver_mi_perfil'),
    path('mis-publicaciones/', MisPublicacionesView.as_view(), name='mis_publicaciones'),
    
    # Notificaciones
    path('notificaciones/', NotificacionesView.as_view(), name='notificaciones'),
    
    # Saldos comerciales
    path('comercio/emitir-vuelto/', EmitirVueltoComercialView.as_view(), name='emitir_vuelto'),
    path('comercios/', CatalogoComerciosView.as_view(), name='catalogo_comercios'),
    path('comercio/pagar/', PagarConSaldoView.as_view(), name='pagar_con_saldo'),
    path('mi-saldo-comercial/', VerSaldoComercialView.as_view(), name='ver_saldo_comercial'),
]

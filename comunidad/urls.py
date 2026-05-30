from django.urls import path
from .views import (
    CargarUsuariosCSVView, 
    RegistroUsuarioView, 
    SesionActualView,
    LoginView,
    LogoutView,
    CarteleraFeedView, 
    FinalizarTruequeView, 
    RegistrarResenaView, 
    EmitirVueltoComercialView,
    MatchmakingView,
    CrearPropuestaView,
    ResponderPropuestaView,
    CatalogoComerciosView,
    PagarConSaldoView
)

# CAMBIO CONTROLADOR: estas rutas son la frontera HTTP que consume la vista Vue.
urlpatterns = [
    path('sesion/', SesionActualView.as_view(), name='sesion_actual'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('cargar-csv/', CargarUsuariosCSVView.as_view(), name='cargar_csv'),
    path('registro/', RegistroUsuarioView.as_view(), name='registro'),
    path('cartelera/', CarteleraFeedView.as_view(), name='cartelera'),
    
    # HU4: Match y Propuestas
    path('matchmaking/', MatchmakingView.as_view(), name='matchmaking'),
    path('trueques/propuestas/crear/', CrearPropuestaView.as_view(), name='crear_propuesta'),
    path('trueques/<int:trueque_id>/responder/', ResponderPropuestaView.as_view(), name='responder_propuesta'),
    
    # HU4: Finalizar y Reseñas
    path('trueques/<int:trueque_id>/finalizar/', FinalizarTruequeView.as_view(), name='finalizar_trueque'),
    path('resenas/', RegistrarResenaView.as_view(), name='registrar_resena'),
    
    path('comercio/emitir-vuelto/', EmitirVueltoComercialView.as_view(), name='emitir_vuelto'),
    path('comercios/', CatalogoComerciosView.as_view(), name='catalogo_comercios'),
    path('comercio/pagar/', PagarConSaldoView.as_view(), name='pagar_con_saldo'),
]

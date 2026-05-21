from django.urls import path
from .views import (
    CargarUsuariosCSVView, 
    RegistroUsuarioView, 
    CarteleraFeedView, 
    FinalizarTruequeView, 
    RegistrarResenaView, 
    EmitirVueltoComercialView
)

urlpatterns = [
    path('cargar-csv/', CargarUsuariosCSVView.as_view(), name='cargar_csv'),
    path('registro/', RegistroUsuarioView.as_view(), name='registro'),
    path('cartelera/', CarteleraFeedView.as_view(), name='cartelera'),
    path('trueques/<int:trueque_id>/finalizar/', FinalizarTruequeView.as_view(), name='finalizar_trueque'),
    path('resenas/', RegistrarResenaView.as_view(), name='registrar_resena'),
    path('comercio/emitir-vuelto/', EmitirVueltoComercialView.as_view(), name='emitir_vuelto'),
]

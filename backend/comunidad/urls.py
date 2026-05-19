from django.urls import path
from .views import (
    ImportarMiembrosView,
    VerificarAutorizacionView,  # 👈 nuevo
)

urlpatterns = [
    path('miembros/importar/', ImportarMiembrosView.as_view(), name='importar-miembros'),
    path('auth/verificar/', VerificarAutorizacionView.as_view(), name='verificar-autorizacion'),  

]
from django.contrib import admin
from .models import (
    AcuerdoTrueque,
    DonacionHoras,
    Publicacion,
    Resena,
    SaldoComercial,
    SolicitudApoyoSocial,
    Usuario,
    UsuarioAutorizado,
)

# Registramos los modelos para que aparezcan en el panel de administración
admin.site.register(Usuario)
admin.site.register(UsuarioAutorizado)
admin.site.register(Publicacion)
admin.site.register(AcuerdoTrueque)
admin.site.register(Resena)
admin.site.register(SaldoComercial)
admin.site.register(SolicitudApoyoSocial)
admin.site.register(DonacionHoras)

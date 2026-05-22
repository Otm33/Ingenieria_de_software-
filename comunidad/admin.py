from django.contrib import admin
from .models import Usuario, Publicacion, AcuerdoTrueque, Resena, SaldoComercial

# Registramos los modelos para que aparezcan en el panel de administración
admin.site.register(Usuario)
admin.site.register(Publicacion)
admin.site.register(AcuerdoTrueque)
admin.site.register(Resena)
admin.site.register(SaldoComercial)

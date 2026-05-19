from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ConfiguracionComunidad, MiembroComunidad, CuentaSaldo

# Registramos los modelos de manera directa
admin.site.register(ConfiguracionComunidad)
admin.site.register(MiembroComunidad)
admin.site.register(CuentaSaldo)
from django.db import models
from django.contrib.auth.models import User #En teoria esta libreria nos va a facilitar la vida al crear el usuario

# PRIMER MODELO Configuración Global de la Comunidad

class ConfiguracionComunidad(models.Model):
    horas_iniciales_base = models.FloatField(default=0.0)
    permitir_excedentes = models.BooleanField(default=False) # Todas las horas valen 1, no vamos a permitir excedentes en un trueque normal
    vigencia_credito_comercial = models.IntegerField(default=12) 

    def __str__(self):
        return f"Configuración Activa (Vigencia: {self.vigencia_credito_comercial} meses)"

    def actualizar_parametros(self, horas, excedentes, vigencia):
        self.horas_iniciales_base = horas
        self.permitir_excedentes = excedentes
        self.vigencia_credito_comercial = vigencia
        self.save()


# SEGUNDO MODELO Miembro de la comunidad (Usuario/Comercio)

class MiembroComunidad(models.Model):
    #Vamos a hacer la relacion 1 a 1 con el user de django para manejar contraseñas y el login seguro
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='miembro_comunidad')

    cedula = models.CharField(max_length=20, unique = True)
    nombre = models.CharField(max_length=150)
    correo = models.EmailField(unique = True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    estado = models.CharField(max_length=50, default='ACTIVO') #Es charfiled y no booleano, pq en cualquier momento los requisitos pueden cambiar, aunque en este momento solo sean dos estados, mas adelante pueden ser 5
    es_administrador = models.BooleanField(default=False)

    # Un usuario solo puede estar vinculado a un comercio a la vez (ForeignKey apunta a sí mismo)
    id_comercio_vinculado = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='miembros_vinculados'
    )

    def __str__(self):
        return f"{self.nombre} ({self.cedula})"

    def registrar_ingreso(self):
        # Lógica que ejecutaremos más adelante cuando el usuario valide su ingreso
        pass

    def suspender_cuenta(self):
        self.estado = 'SUSPENDIDO'
        self.save()

# MODELO 3  Cuenta de Saldo, control de horas del trueque.

class CuentaSaldo(models.Model):
    #Cada miembro tiene una cuenta saldo
    miembro = models.OneToOneField(MiembroComunidad, on_delete= models.CASCADE, related_name='cuenta_saldo')
    saldo_horas = models.FloatField(default = 0.0)
    saldo_comercial_excedente = models.FloatField(default=0.0)
    estado_cuenta = models.CharField(max_length=50, default='ACTIVO')

    def __str__(self):
        return f"Saldos de {self.miembro.nombre}: {self.saldo_horas}h"

    def inicializar_saldos(self, horas):
        self.saldo_horas = horas
        self.save()
        
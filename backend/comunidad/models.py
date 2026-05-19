from django.db import models
from django.contrib.auth.models import User
# Esta librería nos facilita la vida al manejar autenticación, contraseñas y login seguro


# ============================================================
# MODELO 1: Configuración Global de la Comunidad (Singleton)
# ============================================================
class ConfiguracionComunidad(models.Model):
    """
    Configuración global del sistema. 
    Patrón Singleton: solo debe existir UN registro activo.
    """
    horas_iniciales_base = models.FloatField(default=0.0)
    permitir_excedentes = models.BooleanField(default=False)  
    # Todas las horas valen 1; no permitimos excedentes en un trueque normal
    
    vigencia_credito_comercial = models.IntegerField(
        default=12,
        help_text="Vigencia del crédito comercial en meses"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de la Comunidad"
        verbose_name_plural = "Configuración de la Comunidad"

    def __str__(self):
        return f"Configuración Activa (Vigencia: {self.vigencia_credito_comercial} meses)"

    # ---- Patrón Singleton ----
    def save(self, *args, **kwargs):
        # Forzamos siempre el mismo PK para que solo exista un registro
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Bloqueamos la eliminación: la configuración no debe borrarse
        pass

    @classmethod
    def cargar(cls):
        """Devuelve la configuración (la crea con valores por defecto si no existe)."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def actualizar_parametros(self, horas, excedentes, vigencia):
        self.horas_iniciales_base = horas
        self.permitir_excedentes = excedentes
        self.vigencia_credito_comercial = vigencia
        self.save()


# ============================================================
# MODELO 2: Miembro de la Comunidad (Usuario / Comercio)
# ============================================================
class MiembroComunidad(models.Model):
    """
    Representa a un miembro validado de la comunidad.
    Se vincula 1 a 1 con el User de Django para aprovechar el sistema
    de autenticación nativo (contraseñas hasheadas, login, sesiones).
    """

    # ---- Estados posibles del miembro ----
    # Usamos TextChoices: mantenemos flexibilidad de CharField + validación + autodocumentación
    class Estado(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        SUSPENDIDO = 'SUSPENDIDO', 'Suspendido'
        PENDIENTE = 'PENDIENTE', 'Pendiente de validación'
        INACTIVO = 'INACTIVO', 'Inactivo'

    usuario = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='miembro_comunidad'
    )

    cedula = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=150)
    correo = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)

    estado = models.CharField(
        max_length=50,
        choices=Estado.choices,
        default=Estado.ACTIVO
        # Es CharField y no BooleanField porque los requisitos pueden cambiar:
        # hoy son 4 estados, mañana podrían ser 6.
    )

    es_administrador = models.BooleanField(default=False)

    # Un miembro puede estar vinculado a un comercio (que también es un MiembroComunidad)
    id_comercio_vinculado = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='miembros_vinculados'
    )

    # ---- Auditoría ----
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Miembro de la Comunidad"
        verbose_name_plural = "Miembros de la Comunidad"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.cedula})"

    def registrar_ingreso(self):
        # Lógica que ejecutaremos más adelante cuando el usuario valide su ingreso
        pass

    def suspender_cuenta(self):
        self.estado = self.Estado.SUSPENDIDO
        self.save()

    def activar_cuenta(self):
        self.estado = self.Estado.ACTIVO
        self.save()


# ============================================================
# MODELO 3: Cuenta de Saldo (control de horas del trueque)
# ============================================================
class CuentaSaldo(models.Model):
    """
    Cada miembro posee UNA cuenta de saldo asociada.
    Se inicializa al momento del registro con las horas base
    definidas en ConfiguracionComunidad.
    """
    miembro = models.OneToOneField(
        MiembroComunidad, 
        on_delete=models.CASCADE, 
        related_name='cuenta_saldo'
    )
    saldo_horas = models.FloatField(default=0.0)
    estado_cuenta = models.CharField(max_length=50, default='ACTIVO')

    # ---- Auditoría ----
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cuenta de Saldo"
        verbose_name_plural = "Cuentas de Saldo"

    def __str__(self):
        return f"Saldos de {self.miembro.nombre}: {self.saldo_horas}h"

    def inicializar_saldos(self, horas=None):
        """
        Inicializa el saldo. Si no se pasa un valor explícito,
        toma el valor por defecto de la configuración global.
        """
        if horas is None:
            config = ConfiguracionComunidad.cargar()
            horas = config.horas_iniciales_base
        self.saldo_horas = horas
        self.save()
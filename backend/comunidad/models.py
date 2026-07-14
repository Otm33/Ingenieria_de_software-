from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from decimal import Decimal
import uuid


# Esta archivo define solo los modelos Django (ORM).


class UsuarioAutorizado(models.Model):
    """Lista blanca de correos autorizados por el Administrador via CSV."""
    TIPO_CHOICES = [('USUARIO', 'Usuario'), ('COMERCIO', 'Comercio')]

    email = models.EmailField(unique=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='USUARIO')
    cargado_el = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.email} ({self.tipo})"


class Usuario(AbstractUser):
    """Perfil del usuario con balance de Horas de Vida y reputación."""
    ESTADO_SOCIAL_CHOICES = [
        ('NINGUNO', 'Ninguno'),
        ('VULNERABLE', 'Vulnerable'),
        ('CRITICO', 'Crítico'),
    ]

    email = models.EmailField(unique=True)
    nombre_real = models.CharField(max_length=150)
    horas_de_vida = models.FloatField(default=0.0)
    es_comercio = models.BooleanField(default=False)
    saldo_comercial = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    # Sprint 2 HU1: Impacto Social
    estado_social = models.CharField(max_length=15, choices=ESTADO_SOCIAL_CHOICES, default='NINGUNO')
    horas_recibidas_donacion = models.FloatField(default=0.0)
    es_fondo_comunitario = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(horas_de_vida__gte=-10.0), name='limite_balance_negativo_horas')
        ]

    @property
    def promedio_estrellas(self) -> float:
        resenas = self.resenas_recibidas.all()
        if not resenas:
            return 5.0
        return sum(r.estrellas for r in resenas) / resenas.count()

    def __str__(self) -> str:
        return f"{self.username} ({self.nombre_real})"


class Publicacion(models.Model):
    """Catálogo de ofertas (Talentos) y demandas (Necesidades)."""
    TIPO_CHOICES = [('TALENTO', 'Talento'), ('NECESIDAD', 'Necesidad')]
    URGENCIA_CHOICES = [('NORMAL', 'Normal'), ('ALTA', 'Urgencia Alta'), ('CRITICA', 'Necesidad Crítica')]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='publicaciones')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=80, db_index=True)
    urgencia = models.CharField(max_length=10, choices=URGENCIA_CHOICES, default='NORMAL', db_index=True)
    esta_activa = models.BooleanField(default=True)
    es_causa_social = models.BooleanField(default=False)


class AcuerdoTrueque(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),       # Propuesta enviada, sin respuesta
        ('EN_CURSO', 'En Curso'),          # Receptor aceptó, servicio en progreso
        ('ACEPTADO', 'Aceptado'),          # Código ingresado, pendiente de reseñas
        ('FINALIZADO', 'Finalizado'),      # Ambos calificaron
        ('RECHAZADO', 'Rechazado'),
    )

    emisor = models.ForeignKey(Usuario, related_name='trueques_enviados', on_delete=models.CASCADE)
    receptor = models.ForeignKey(Usuario, related_name='trueques_recibidos', on_delete=models.CASCADE)
    estado = models.CharField(max_length=15, choices=ESTADOS, default='PENDIENTE')

    publicacion_emisor = models.ForeignKey('Publicacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='trueques_como_emisor')
    publicacion_receptor = models.ForeignKey('Publicacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='trueques_como_receptor')

    emisor_confirmado = models.BooleanField(default=False)
    receptor_confirmado = models.BooleanField(default=False)

    creado_el = models.DateTimeField(auto_now_add=True, null=True)
    actualizado_el = models.DateTimeField(auto_now=True, null=True)

    codigo_confirmacion = models.CharField(max_length=8, unique=True, null=True, blank=True)


class Resena(models.Model):
    trueque = models.ForeignKey(AcuerdoTrueque, on_delete=models.CASCADE, related_name='resenas')
    calificador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='resenas_emitidadas')
    calificado = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='resenas_recibidas')
    estrellas = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(max_length=500)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['trueque', 'calificador'], name='una_resena_por_usuario_por_trueque')]


class NotificacionPropuesta(models.Model):
    TIPO_CHOICES = [('MATCH', 'Match'), ('PROPUESTA', 'Propuesta'), ('RESENA', 'Reseña')]
    ESTADOS = (('PENDIENTE', 'Pendiente'), ('ACEPTADA', 'Aceptada'), ('RECHAZADA', 'Rechazada'), ('LEIDA', 'Leída'))

    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='PROPUESTA')
    destinatario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones_recibidas')
    remitente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones_enviadas')
    trueque = models.ForeignKey(AcuerdoTrueque, on_delete=models.CASCADE, related_name='notificaciones', null=True, blank=True)
    publicacion_original = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='notificaciones', null=True, blank=True)
    trueque_multiple = models.ForeignKey('AcuerdoTruequeMultiple', on_delete=models.CASCADE, related_name='notificaciones_multiple', null=True, blank=True)
    mensaje = models.TextField(max_length=300)
    match_detalle = models.JSONField(null=True, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADOS, default='PENDIENTE')
    creada_el = models.DateTimeField(auto_now_add=True)
    leida_el = models.DateTimeField(null=True, blank=True)
    prioridad = models.BooleanField(default=True)

    class Meta:
        ordering = ['-prioridad', '-creada_el']


class SaldoComercial(models.Model):
    TIPO_MOVIMIENTO = [('EMISION', 'Emisión de vuelto'), ('PAGO', 'Pago en comercio')]
    comercio = models.ForeignKey(Usuario, related_name='operaciones_comerciales', on_delete=models.CASCADE)
    cliente = models.ForeignKey(Usuario, related_name='movimientos_saldo', on_delete=models.CASCADE)
    monto_excedente = models.DecimalField(max_digits=10, decimal_places=2)
    valor_producto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    monto_recibido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO, default='EMISION')
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)


class AcuerdoTruequeMultiple(models.Model):
    ESTADOS = (('PENDIENTE', 'Pendiente'), ('ACEPTADO', 'Aceptado'), ('RECHAZADO', 'Rechazado'), ('EN_CURSO', 'En Curso'), ('FINALIZADO', 'Finalizado'), ('EXPIRADO', 'Expirado'))

    emisor1 = models.ForeignKey(Usuario, related_name='trueques_multiple_emisor1', on_delete=models.CASCADE)
    receptor1 = models.ForeignKey(Usuario, related_name='trueques_multiple_receptor1', on_delete=models.CASCADE)
    emisor2 = models.ForeignKey(Usuario, related_name='trueques_multiple_emisor2', on_delete=models.CASCADE)
    receptor2 = models.ForeignKey(Usuario, related_name='trueques_multiple_receptor2', on_delete=models.CASCADE)
    emisor3 = models.ForeignKey(Usuario, related_name='trueques_multiple_emisor3', on_delete=models.CASCADE)
    receptor3 = models.ForeignKey(Usuario, related_name='trueques_multiple_receptor3', on_delete=models.CASCADE)

    publicacion_emisor1 = models.ForeignKey('Publicacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='trueques_multiple_emisor1')
    publicacion_receptor1 = models.ForeignKey('Publicacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='trueques_multiple_receptor1')
    publicacion_emisor2 = models.ForeignKey('Publicacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='trueques_multiple_emisor2')
    publicacion_receptor2 = models.ForeignKey('Publicacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='trueques_multiple_receptor2')
    publicacion_emisor3 = models.ForeignKey('Publicacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='trueques_multiple_emisor3')
    publicacion_receptor3 = models.ForeignKey('Publicacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='trueques_multiple_receptor3')

    estado = models.CharField(max_length=15, choices=ESTADOS, default='PENDIENTE')
    usuario1_aceptado = models.BooleanField(default=False)
    usuario2_aceptado = models.BooleanField(default=False)
    usuario3_aceptado = models.BooleanField(default=False)

    par1_confirmado = models.BooleanField(default=False)
    par2_confirmado = models.BooleanField(default=False)
    par3_confirmado = models.BooleanField(default=False)

    codigo_par1 = models.CharField(max_length=8, unique=True, null=True, blank=True)
    codigo_par2 = models.CharField(max_length=8, unique=True, null=True, blank=True)
    codigo_par3 = models.CharField(max_length=8, unique=True, null=True, blank=True)

    creado_el = models.DateTimeField(auto_now_add=True)
    actualizado_el = models.DateTimeField(auto_now=True)
    expira_el = models.DateTimeField()

    class Meta:
        constraints = []

class ResenaMultiple(models.Model):
    trueque_multiple = models.ForeignKey(AcuerdoTruequeMultiple, on_delete=models.CASCADE, related_name='resenas_multiple')
    calificador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='resenas_multiple_emitidas')
    calificado = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='resenas_multiple_recibidas')
    estrellas = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(max_length=500)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['trueque_multiple', 'calificador', 'calificado'], name='una_resena_multiple_por_calificador_por_calificado')]


# ── Sprint 2 HU1: Impacto Social ─────────────────────────────────────────────

class SolicitudApoyoSocial(models.Model):
    """Sprint 2 HU1: Solicitudes de apoyo social publicadas por usuarios."""
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
    )

    solicitante = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='solicitudes_apoyo',
    )
    categoria = models.CharField(max_length=80, blank=True, default='')
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField()
    estado = models.CharField(max_length=15, choices=ESTADOS, default='PENDIENTE')
    horas_recibidas = models.FloatField(default=0.0)
    horas_solidarias_disponibles = models.FloatField(default=0.0)
    horas_solidarias_utilizadas = models.FloatField(default=0.0)
    publicacion = models.OneToOneField(
        'Publicacion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitud_apoyo_social',
    )
    aprobada_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitudes_aprobadas',
    )
    creado_el = models.DateTimeField(auto_now_add=True)
    actualizado_el = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.titulo} ({self.estado})"


class DonacionHoras(models.Model):
    """Sprint 2 HU1: Ledger irreversible de donaciones de Horas de Vida."""
    TIPO_DESTINO_CHOICES = [
        ('CAUSA', 'Causa'),
        ('FONDO', 'Fondo'),
        ('ASIGNACION', 'Asignación desde fondo'),
    ]

    donante = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='donaciones_realizadas',
    )
    receptor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='donaciones_recibidas',
    )
    solicitud = models.ForeignKey(
        SolicitudApoyoSocial,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='donaciones',
    )
    monto = models.FloatField()
    tipo_destino = models.CharField(max_length=10, choices=TIPO_DESTINO_CHOICES)
    fecha = models.DateTimeField(auto_now_add=True)
    comprobante_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    def __str__(self) -> str:
        return f"Donación {self.monto}h → {self.receptor} ({self.tipo_destino})"

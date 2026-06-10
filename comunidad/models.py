from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal

# CAMBIO MODELO: este archivo queda como la unica capa de modelos Django persistidos en BD.

class UsuarioAutorizado(models.Model):
    """HU1: Lista blanca de correos autorizados por el Administrador via CSV."""
    TIPO_CHOICES = [('USUARIO', 'Usuario'), ('COMERCIO', 'Comercio')]

    email = models.EmailField(unique=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='USUARIO')
    cargado_el = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} ({self.tipo})"

class Usuario(AbstractUser):
    """HU2: Perfil del usuario con balance de Horas de Vida y reputación."""
    email = models.EmailField(unique=True)
    nombre_real = models.CharField(max_length=150) # HU2: Evitar anonimato
    horas_de_vida = models.FloatField(default=0.0)
    es_comercio = models.BooleanField(default=False) # HU5: Identificador de comercio
    saldo_comercial = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        constraints = [
            # Requisito: Ningún usuario puede deber más de 10 créditos (horas)
            models.CheckConstraint(
                condition=models.Q(horas_de_vida__gte=-10.0),
                name="limite_balance_negativo_horas"
            )
        ]

    @property
    def promedio_estrellas(self):
        resenas = self.resenas_recibidas.all()
        if not resenas:
            return 5.0
        return sum(r.estrellas for r in resenas) / resenas.count()

    def __str__(self):
        return f"{self.username} ({self.nombre_real})"

class Publicacion(models.Model):
    """HU2 y HU3: Catálogo de ofertas (Talentos) y demandas (Necesidades)."""
    TIPO_CHOICES = [('TALENTO', 'Talento'), ('NECESIDAD', 'Necesidad')]
    URGENCIA_CHOICES = [('NORMAL', 'Normal'), ('ALTA', 'Urgencia Alta'), ('CRITICA', 'Necesidad Crítica')]
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='publicaciones')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=80, db_index=True) # db_index para búsquedas rápidas (<1.5s)
    urgencia = models.CharField(max_length=10, choices=URGENCIA_CHOICES, default='NORMAL', db_index=True)
    esta_activa = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # HU1 Límite: Máximo 5 talentos publicados simultáneamente
        if self.tipo == 'TALENTO' and self.esta_activa:
            conteo = Publicacion.objects.filter(usuario=self.usuario, tipo='TALENTO', esta_activa=True).count()
            if conteo >= 5 and not self.pk:
                raise ValidationError("No puedes tener más de 5 talentos activos publicados simultáneamente.")
        
        # HU2 Límite: Máximo 3 necesidades activas
        if self.tipo == 'NECESIDAD' and self.esta_activa:
            conteo = Publicacion.objects.filter(usuario=self.usuario, tipo='NECESIDAD', esta_activa=True).count()
            if conteo >= 3 and not self.pk:
                raise ValidationError("No puedes tener más de 3 necesidades activas simultáneamente.")
                
        # HU2 Restricción 3: Un usuario con un saldo menor a -10 horas no puede pausar ofertas (o alterarlas)
        if self.usuario.horas_de_vida < -10.0:
            raise ValidationError("Saldo crítico inferior a -10 horas. Operación bloqueada.")

        if self.tipo == "TALENTO" and self.urgencia != "NORMAL":
            raise ValidationError("Los talentos solo pueden tener urgencia Normal.")
            
        super().save(*args, **kwargs)

class AcuerdoTrueque(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('ACEPTADO', 'Aceptado'),
        ('RECHAZADO', 'Rechazado'),
        ('EN_CURSO', 'En Curso'),
        ('FINALIZADO', 'Finalizado'),
    )
    emisor = models.ForeignKey(Usuario, related_name='trueques_enviados', on_delete=models.CASCADE)
    receptor = models.ForeignKey(Usuario, related_name='trueques_recibidos', on_delete=models.CASCADE)
    estado = models.CharField(max_length=15, choices=ESTADOS, default='PENDIENTE')
    
    # Referencias a las publicaciones específicas involucradas
    publicacion_emisor = models.ForeignKey('Publicacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='trueques_como_emisor')
    publicacion_receptor = models.ForeignKey('Publicacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='trueques_como_receptor')
    
    # Para la confirmación de ambas partes antes de transferir el saldo
    emisor_confirmado = models.BooleanField(default=False)
    receptor_confirmado = models.BooleanField(default=False)
    
    # Fecha de creación y modificación
    creado_el = models.DateTimeField(auto_now_add=True, null=True)  # null=True para migraciones
    actualizado_el = models.DateTimeField(auto_now=True, null=True)  # null=True para migraciones

class Resena(models.Model):
    """HU4: Calificaciones e historial de confianza post-trueque."""
    trueque = models.ForeignKey(AcuerdoTrueque, on_delete=models.CASCADE, related_name='resenas')
    calificador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='resenas_emitidadas')
    calificado = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='resenas_recibidas')
    estrellas = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(max_length=500) # Restricción estricta de 500 caracteres

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['trueque', 'calificador'],
                name='una_resena_por_usuario_por_trueque',
            ),
        ]

class NotificacionPropuesta(models.Model):
    """Notificaciones para propuestas de trueque que aparecen en la cartelera."""
    TIPO_CHOICES = [('MATCH', 'Match'), ('PROPUESTA', 'Propuesta')]
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('ACEPTADA', 'Aceptada'),
        ('RECHAZADA', 'Rechazada'),
        ('LEIDA', 'Leída'),
    )

    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='PROPUESTA')
    destinatario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones_recibidas')
    remitente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones_enviadas')
    trueque = models.ForeignKey(AcuerdoTrueque, on_delete=models.CASCADE, related_name='notificaciones')
    publicacion_original = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='notificaciones')
    mensaje = models.TextField(max_length=300)
    match_detalle = models.JSONField(null=True, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADOS, default='PENDIENTE')
    creada_el = models.DateTimeField(auto_now_add=True)
    leida_el = models.DateTimeField(null=True, blank=True)
    prioridad = models.BooleanField(default=True) # Si es True, aparece primero en la cartelera
    
    class Meta:
        ordering = ['-prioridad', '-creada_el']

class SaldoComercial(models.Model):
    TIPO_MOVIMIENTO = [
        ('EMISION', 'Emisión de vuelto'),
        ('PAGO', 'Pago en comercio'),
    ]
    comercio = models.ForeignKey(Usuario, related_name='operaciones_comerciales', on_delete=models.CASCADE)
    cliente = models.ForeignKey(Usuario, related_name='movimientos_saldo', on_delete=models.CASCADE)
    monto_excedente = models.DecimalField(max_digits=10, decimal_places=2)
    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO, default='EMISION')
    fecha = models.DateTimeField(auto_now_add=True)

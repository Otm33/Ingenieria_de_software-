from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db import models
from decimal import Decimal

class UsuarioAutorizado(models.Model):
    """HU1: Lista blanca de correos autorizados por el Administrador via CSV."""
    email = models.EmailField(unique=True)
    cargado_el = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

class Usuario(AbstractUser):
    """HU2: Perfil del usuario con balance de Horas de Vida y reputación."""
    email = models.EmailField(unique=True)
    nombre_real = models.CharField(max_length=150) # HU2: Evitar anonimato
    horas_de_vida = models.FloatField(default=0.0)
    promedio_estrellas = models.FloatField(default=5.0)
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
    categoria = models.CharField(max_length=50, db_index=True) # db_index para búsquedas rápidas (<1.5s)
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
            
        super().save(*args, **kwargs)

class AcuerdoTrueque(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('ACEPTADO', 'Aceptado'),
        ('RECHAZADO', 'Rechazado'),
        ('FINALIZADO', 'Finalizado'),
    )
    emisor = models.ForeignKey(Usuario, related_name='trueques_enviados', on_delete=models.CASCADE)
    receptor = models.ForeignKey(Usuario, related_name='trueques_recibidos', on_delete=models.CASCADE)
    estado = models.CharField(max_length=15, choices=ESTADOS, default='PENDIENTE')
    
    # NUEVO: Para la confirmación de ambas partes antes de transferir el saldo
    emisor_confirmado = models.BooleanField(default=False)
    receptor_confirmado = models.BooleanField(default=False)

class Resena(models.Model):
    """HU4: Calificaciones e historial de confianza post-trueque."""
    trueque = models.OneToOneField(AcuerdoTrueque, on_delete=models.CASCADE, related_name='resena')
    calificador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='resenas_emitidadas')
    calificado = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='resenas_recibidas')
    estrellas = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(max_length=500) # Restricción estricta de 500 caracteres

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

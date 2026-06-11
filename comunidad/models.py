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

    # ===== MÉTODOS DE NEGOCIO =====
    
    def puede_publicar(self, tipo_publicacion):
        """
        Verifica si el usuario puede publicar según su saldo y límites.
        HU1: Máximo 5 talentos activos simultáneamente
        HU2: Máximo 3 necesidades activas simultáneamente
        HU2: Usuario con saldo menor a -10 horas no puede modificar ofertas
        """
        if self.tiene_saldo_critico():
            return False, "Saldo crítico inferior a -10 horas. No puedes publicar."
        
        conteo = self.publicaciones.filter(tipo=tipo_publicacion, esta_activa=True).count()
        
        if tipo_publicacion == 'TALENTO' and conteo >= 5:
            return False, "No puedes tener más de 5 talentos activos publicados simultáneamente."
        
        if tipo_publicacion == 'NECESIDAD' and conteo >= 3:
            return False, "No puedes tener más de 3 necesidades activas simultáneamente."
        
        return True, "Puede publicar"
    
    def tiene_saldo_critico(self):
        """HU2: Verifica si el usuario tiene saldo menor a -10 horas."""
        return self.horas_de_vida < -10.0
    
    def puede_modificar_publicaciones(self):
        """HU2: Usuario con saldo menor a -10 horas no puede modificar ofertas."""
        return not self.tiene_saldo_critico()
    
    def es_comercio_activo(self):
        """HU5: Verifica si es un comercio activo."""
        return self.es_comercio and self.is_active
    
    def es_miembro_activo(self):
        """HU2: Verifica si es un miembro activo (tiene publicaciones y nombre real)."""
        nombre = (self.nombre_real or "").strip()
        tiene_publicaciones = self.publicaciones.exists()
        return bool(nombre and tiene_publicaciones)
    
    def puede_realizar_trueque(self):
        """Verifica si el usuario puede realizar trueques (no tiene saldo crítico)."""
        return not self.tiene_saldo_critico()
    
    def obtener_talentos_principales(self):
        """Retorna los títulos de los talentos activos del usuario."""
        return list(
            self.publicaciones.filter(tipo='TALENTO', esta_activa=True)
            .values_list('titulo', flat=True)
        )
    
    def puede_emitir_vuelto_comercial(self, monto):
        """HU5: Verifica si el comercio puede emitir vuelto (saldo comercial suficiente)."""
        if not self.es_comercio_activo():
            return False, "Solo los comercios activos pueden emitir vuelto."
        if self.saldo_comercial < monto:
            return False, "Saldo comercial insuficiente para emitir vuelto."
        return True, "Puede emitir vuelto"
    
    def puede_pagar_con_saldo(self, monto):
        """HU5: Verifica si el cliente puede pagar con saldo comercial."""
        if self.es_comercio:
            return False, "Los comercios no pueden pagar con saldo comercial."
        if self.saldo_comercial < monto:
            return False, "Saldo comercial insuficiente."
        return True, "Puede pagar con saldo"

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
        # Validar reglas de negocio antes de guardar
        es_valido, mensaje = self.validar_reglas_negocio()
        if not es_valido:
            raise ValidationError(mensaje)
        super().save(*args, **kwargs)

    # ===== MÉTODOS DE NEGOCIO =====
    
    def es_talento(self):
        """HU2/HU3: Verifica si esta publicación es un talento."""
        return self.tipo == 'TALENTO'
    
    def es_necesidad(self):
        """HU2/HU3: Verifica si esta publicación es una necesidad."""
        return self.tipo == 'NECESIDAD'
    
    def validar_reglas_negocio(self):
        """
        Valida todas las reglas de negocio antes de crear/modificar una publicación.
        HU1: Máximo 5 talentos activos simultáneamente
        HU2: Máximo 3 necesidades activas simultáneamente
        HU2: Usuario con saldo menor a -10 horas no puede modificar ofertas
        Restricción: Los talentos solo pueden tener urgencia Normal
        """
        # Verificar si el usuario puede modificar publicaciones
        if not self.usuario.puede_modificar_publicaciones():
            return False, "Saldo crítico inferior a -10 horas. Operación bloqueada."
        
        # Validar urgencia para talentos
        if self.es_talento() and self.urgencia != "NORMAL":
            return False, "Los talentos solo pueden tener urgencia Normal."
        
        # Validar límites de publicaciones (solo al crear)
        if not self.pk and self.esta_activa:
            puede_publicar, mensaje = self.usuario.puede_publicar(self.tipo)
            if not puede_publicar:
                return False, mensaje
        
        return True, "Validación exitosa"
    
    def puede_pausarse(self):
        """Verifica si la publicación puede pausarse (usuario tiene saldo suficiente)."""
        return self.usuario.puede_modificar_publicaciones()
    
    def puede_reactivarse(self):
        """Verifica si la publicación puede reactivarse."""
        if not self.esta_activa:
            puede_publicar, mensaje = self.usuario.puede_publicar(self.tipo)
            return puede_publicar, mensaje
        return False, "La publicación ya está activa"
    
    def es_urgente(self):
        """HU3: Verifica si la publicación tiene urgencia alta o crítica."""
        return self.urgencia in ['ALTA', 'CRITICA']
    
    def es_critica(self):
        """HU3: Verifica si la publicación es crítica."""
        return self.urgencia == 'CRITICA'
    
    def obtener_prioridad_urgencia(self):
        """HU3: Retorna la prioridad numérica para ordenamiento."""
        prioridades = {'CRITICA': 3, 'ALTA': 2, 'NORMAL': 1}
        return prioridades.get(self.urgencia, 0)
    
    def coincide_con_categoria(self, categoria):
        """HU3: Verifica si la publicación coincide con la categoría dada."""
        return self.categoria == categoria
    
    def coincide_con_urgencia(self, urgencias):
        """HU3: Verifica si la publicación coincide con alguna de las urgencias dadas."""
        return self.urgencia in urgencias

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

    # ===== MÉTODOS DE NEGOCIO =====
    
    def esta_pendiente(self):
        """HU4: Verifica si el trueque está en estado pendiente."""
        return self.estado == 'PENDIENTE'
    
    def esta_aceptado(self):
        """HU4: Verifica si el trueque ha sido aceptado."""
        return self.estado == 'ACEPTADO'
    
    def esta_rechazado(self):
        """HU4: Verifica si el trueque ha sido rechazado."""
        return self.estado == 'RECHAZADO'
    
    def esta_en_curso(self):
        """HU4: Verifica si el trueque está en curso."""
        return self.estado == 'EN_CURSO'
    
    def esta_finalizado(self):
        """HU4: Verifica si el trueque está finalizado."""
        return self.estado == 'FINALIZADO'
    
    def puede_confirmar(self, usuario):
        """
        HU4: Verifica si un usuario puede confirmar la finalización del trueque.
        Ambas partes deben confirmar antes de transferir el saldo.
        """
        if not self.esta_en_curso():
            return False, "Solo se pueden confirmar trueques en curso."
        
        if usuario == self.emisor:
            return True, "Emisor puede confirmar"
        
        if usuario == self.receptor:
            return True, "Receptor puede confirmar"
        
        return False, "Usuario no es parte del trueque."
    
    def ambas_partes_confirmaron(self):
        """HU4: Verifica si ambas partes han confirmado la finalización."""
        return self.emisor_confirmado and self.receptor_confirmado
    
    def puede_finalizar(self):
        """
        HU4: Verifica si el trueque puede finalizarse.
        Requiere que ambas partes hayan confirmado.
        """
        return self.ambas_partes_confirmaron()
    
    def es_intercambio_mutuo(self):
        """
        HU4: Verifica si es un intercambio mutuo (ambas partes ofrecen algo).
        Ocurre cuando ambas publicaciones son del mismo tipo (ambos talentos o ambas necesidades).
        """
        if not self.publicacion_emisor or not self.publicacion_receptor:
            return False
        return self.publicacion_emisor.tipo == self.publicacion_receptor.tipo
    
    def calcular_impacto_horas(self, usuario):
        """
        HU4: Calcula el impacto en horas de vida para un usuario.
        Emisor de necesidad pierde 1 hora, receptor de talento gana 1 hora.
        """
        if self.es_intercambio_mutuo():
            return 0  # Intercambio equilibrado
        
        if usuario == self.emisor:
            if self.publicacion_emisor and self.publicacion_emisor.es_necesidad():
                return -1  # Emisor pierde 1 hora
            elif self.publicacion_emisor and self.publicacion_emisor.es_talento():
                return 1  # Emisor gana 1 hora
        
        if usuario == self.receptor:
            if self.publicacion_receptor and self.publicacion_receptor.es_talento():
                return 1  # Receptor gana 1 hora
            elif self.publicacion_receptor and self.publicacion_receptor.es_necesidad():
                return -1  # Receptor pierde 1 hora
        
        return 0
    
    def participante(self, usuario):
        """Verifica si el usuario es parte del trueque (emisor o receptor)."""
        return usuario == self.emisor or usuario == self.receptor
    
    def contraparte(self, usuario):
        """Retorna la contraparte del usuario en el trueque."""
        if usuario == self.emisor:
            return self.receptor
        elif usuario == self.receptor:
            return self.emisor
        return None

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

    # ===== MÉTODOS DE NEGOCIO =====
    
    def calificacion_valida(self):
        """HU4: Verifica que la calificación esté entre 1 y 5 estrellas."""
        return 1 <= self.estrellas <= 5
    
    def comentario_valido(self):
        """HU4: Verifica que el comentario no esté vacío y cumpla la longitud máxima."""
        if not self.comentario or not self.comentario.strip():
            return False, "El comentario no puede estar vacío."
        if len(self.comentario) > 500:
            return False, "El comentario no puede exceder 500 caracteres."
        return True, "Comentario válido"
    
    def validar_resena(self):
        """HU4: Valida la reseña completa (calificación y comentario)."""
        if not self.calificacion_valida():
            return False, "La calificación debe estar entre 1 y 5 estrellas."
        
        comentario_valido, mensaje = self.comentario_valido()
        if not comentario_valido:
            return False, mensaje
        
        return True, "Resena válida"
    
    def es_positiva(self):
        """HU4: Verifica si la reseña es positiva (4 o más estrellas)."""
        return self.estrellas >= 4
    
    def es_neutral(self):
        """HU4: Verifica si la reseña es neutral (3 estrellas)."""
        return self.estrellas == 3
    
    def es_negativa(self):
        """HU4: Verifica si la reseña es negativa (1 o 2 estrellas)."""
        return self.estrellas <= 2
    
    def partes_son_participantes_trueque(self):
        """
        HU4: Verifica que calificador y calificado sean participantes del trueque.
        """
        return self.trueque.participante(self.calificador) and self.trueque.participante(self.calificado)
    
    def calificador_es_contraparte(self):
        """HU4: Verifica que el calificador sea la contraparte del calificado en el trueque."""
        return self.trueque.contraparte(self.calificador) == self.calificado

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

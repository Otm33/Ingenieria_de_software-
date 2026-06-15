from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from decimal import Decimal


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
    email = models.EmailField(unique=True)
    nombre_real = models.CharField(max_length=150)
    horas_de_vida = models.FloatField(default=0.0)
    es_comercio = models.BooleanField(default=False)
    saldo_comercial = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

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

    # Compatibilidad: métodos de negocio utilizados por servicios
    def tiene_saldo_critico(self) -> bool:
        return self.horas_de_vida < -10.0

    def puede_publicar(self, tipo_publicacion: str, conteo_actual: int | None = None) -> tuple[bool, str]:
        if self.tiene_saldo_critico():
            return False, "Saldo crítico inferior a -10 horas. No puedes publicar."

        # Si no se provee conteo_actual, calcular desde la BD
        if conteo_actual is None:
            conteo_actual = Publicacion.objects.filter(usuario=self, tipo=tipo_publicacion, esta_activa=True).count()

        if tipo_publicacion == 'TALENTO' and conteo_actual >= 5:
            return False, "No puedes tener más de 5 talentos activos publicados simultáneamente."

        if tipo_publicacion == 'NECESIDAD' and conteo_actual >= 3:
            return False, "No puedes tener más de 3 necesidades activas simultáneamente."

        return True, "Puede publicar"

    def puede_modificar_publicaciones(self) -> bool:
        return not self.tiene_saldo_critico()

    def es_comercio_activo(self) -> bool:
        """Verifica si es un comercio afiliado activo."""
        return self.es_comercio and self.is_active

    def puede_emitir_vuelto_comercial(self, monto) -> tuple[bool, str]:
        """Verifica si el comercio puede emitir vuelto comercial (deuda permitida)."""
        if not self.es_comercio_activo():
            return False, "Solo los comercios activos pueden emitir vuelto."
        return True, "Puede emitir vuelto"

    def puede_pagar_con_saldo(self, monto) -> tuple[bool, str]:
        """Verifica si el cliente puede pagar con saldo comercial."""
        if self.es_comercio:
            return False, "Los comercios no pueden pagar con saldo comercial."
        if self.saldo_comercial < monto:
            return False, "Saldo comercial insuficiente."
        return True, "Puede pagar con saldo"


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

    # Métodos de negocio ligeros para compatibilidad con servicios
    def es_talento(self) -> bool:
        return self.tipo == 'TALENTO'

    def es_necesidad(self) -> bool:
        return self.tipo == 'NECESIDAD'

    def es_urgente(self) -> bool:
        return self.urgencia in ['ALTA', 'CRITICA']

    def es_critica(self) -> bool:
        return self.urgencia == 'CRITICA'

    def validar_reglas_negocio(self, usuario: Usuario | None = None, conteo_actual: int | None = None, es_nueva: bool = True) -> tuple[bool, str]:
        # Verificar saldo crítico si se proporciona usuario
        if usuario and usuario.tiene_saldo_critico():
            return False, "Saldo crítico inferior a -10 horas. Operación bloqueada."

        if self.es_talento() and self.urgencia != "NORMAL":
            return False, "Los talentos solo pueden tener urgencia Normal."

        # Verificar que el usuario no tenga una publicación con el mismo título
        if es_nueva and usuario:
            titulo_existente = Publicacion.objects.filter(
                usuario=usuario,
                titulo__iexact=self.titulo
            ).exists()
            if titulo_existente:
                return False, "Ya tienes una publicación con este título. Por favor usa un título diferente."

        if es_nueva and self.esta_activa and usuario:
            if conteo_actual is None:
                conteo_actual = Publicacion.objects.filter(usuario=usuario, tipo=self.tipo, esta_activa=True).count()
            puede, msj = usuario.puede_publicar(self.tipo, conteo_actual)
            if not puede:
                return False, msj

        return True, "Validación exitosa"

    def puede_pausarse(self) -> tuple[bool, str]:
        return True, "Puede pausar"

    def puede_reactivarse(self) -> tuple[bool, str]:
        # Reutilizar validar_reglas_negocio para comprobar límites al reactivar
        usuario = self.usuario
        conteo_actual = Publicacion.objects.filter(usuario=usuario, tipo=self.tipo, esta_activa=True).exclude(id=self.id).count()
        return self.validar_reglas_negocio(usuario=usuario, conteo_actual=conteo_actual, es_nueva=False)


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

    publicacion_emisor = models.ForeignKey('Publicacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='trueques_como_emisor')
    publicacion_receptor = models.ForeignKey('Publicacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='trueques_como_receptor')

    emisor_confirmado = models.BooleanField(default=False)
    receptor_confirmado = models.BooleanField(default=False)

    creado_el = models.DateTimeField(auto_now_add=True, null=True)
    actualizado_el = models.DateTimeField(auto_now=True, null=True)

    codigo_confirmacion = models.CharField(max_length=8, unique=True, null=True, blank=True)

    # Métodos de negocio ligeros para compatibilidad
    def esta_pendiente(self) -> bool:
        return self.estado == 'PENDIENTE'

    def esta_aceptado(self) -> bool:
        return self.estado == 'ACEPTADO'

    def esta_en_curso(self) -> bool:
        return self.estado == 'EN_CURSO'

    def esta_finalizado(self) -> bool:
        return self.estado == 'FINALIZADO'

    def ambas_partes_confirmaron(self) -> bool:
        return self.emisor_confirmado and self.receptor_confirmado

    def puede_confirmar(self, usuario) -> tuple[bool, str]:
        # Aceptar confirmaciones cuando el trueque está ACEPTADO o EN_CURSO
        if self.estado not in ('ACEPTADO', 'EN_CURSO'):
            return False, "Solo se pueden confirmar trueques en curso."
        if isinstance(usuario, Usuario):
            if usuario.id in (self.emisor_id, self.receptor_id):
                return True, "Puede confirmar"
        else:
            try:
                uid = int(usuario)
            except Exception:
                return False, "Usuario inválido"
            if uid in (self.emisor_id, self.receptor_id):
                return True, "Puede confirmar"
        return False, "Usuario no es parte del trueque."

    def esta_expirado(self):
        """Verifica si el trueque múltiple ha expirado."""
        from django.utils import timezone
        return timezone.now() > self.expira_el

    def participante(self, usuario) -> bool:
        if isinstance(usuario, Usuario):
            return usuario.id in (self.emisor_id, self.receptor_id)
        try:
            uid = int(usuario)
            return uid in (self.emisor_id, self.receptor_id)
        except Exception:
            return False

    def es_intercambio_mutuo(self) -> bool:
        if not self.publicacion_emisor or not self.publicacion_receptor:
            return False
        return self.publicacion_emisor.tipo == 'TALENTO' and self.publicacion_receptor.tipo == 'TALENTO'

    def contraparte(self, usuario):
        if isinstance(usuario, Usuario):
            uid = usuario.id
        else:
            try:
                uid = int(usuario)
            except Exception:
                return None
        if uid == self.emisor_id:
            return self.receptor
        if uid == self.receptor_id:
            return self.emisor
        return None


class Resena(models.Model):
    trueque = models.ForeignKey(AcuerdoTrueque, on_delete=models.CASCADE, related_name='resenas')
    calificador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='resenas_emitidadas')
    calificado = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='resenas_recibidas')
    estrellas = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(max_length=500)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['trueque', 'calificador'], name='una_resena_por_usuario_por_trueque')]

    # Validación de reseña ligera para compatibilidad con servicios
    def validar_resena(self) -> tuple[bool, str]:
        if not (1 <= int(self.estrellas) <= 5):
            return False, "La calificación debe estar entre 1 y 5 estrellas."
        if not self.comentario or not str(self.comentario).strip():
            return False, "El comentario no puede estar vacío."
        if len(self.comentario) > 500:
            return False, "El comentario no puede exceder 500 caracteres."
        return True, "Reseña válida"


class NotificacionPropuesta(models.Model):
    TIPO_CHOICES = [('MATCH', 'Match'), ('PROPUESTA', 'Propuesta')]
    ESTADOS = (('PENDIENTE', 'Pendiente'), ('ACEPTADA', 'Aceptada'), ('RECHAZADA', 'Rechazada'), ('LEIDA', 'Leída'))

    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='PROPUESTA')
    destinatario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones_recibidas')
    remitente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones_enviadas')
    trueque = models.ForeignKey(AcuerdoTrueque, on_delete=models.CASCADE, related_name='notificaciones', null=True, blank=True)
    publicacion_original = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='notificaciones')
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

    def esta_expirado(self):
        """Verifica si el trueque múltiple ha expirado."""
        from django.utils import timezone
        return timezone.now() > self.expira_el

    def participante(self, usuario) -> bool:
        uid = usuario.id if isinstance(usuario, Usuario) else None
        if uid is None:
            try:
                uid = int(usuario)
            except Exception:
                return False
        return uid in (
            self.emisor1_id, self.receptor1_id,
            self.emisor2_id, self.receptor2_id,
            self.emisor3_id, self.receptor3_id,
        )


    def obtener_usuario_por_rol(self, usuario):
        """Retorna el rol del usuario en el trueque múltiple (1, 2 o 3)."""
        uid = usuario.id if isinstance(usuario, Usuario) else usuario
        # Preferir la correspondencia por emisor (participante único):
        if uid == self.emisor1_id:
            return 1
        if uid == self.emisor2_id:
            return 2
        if uid == self.emisor3_id:
            return 3
        # Fallback: si no coincide con emisor, permitir aceptar desde la posición
        # receptor correspondiente (por compatibilidad con notificaciones).
        if uid == self.receptor1_id:
            return 1
        if uid == self.receptor2_id:
            return 2
        if uid == self.receptor3_id:
            return 3
        return None

    def todos_aceptaron(self) -> bool:
        """Verifica si todos los participantes (emisores del ciclo) aceptaron.

        Usamos las posiciones 'emisor1/emisor2/emisor3' como referencia de los
        participantes únicos del ciclo. Si un mismo usuario aparece como emisor
        en varias posiciones, basta con que haya aceptado en alguna de ellas.
        """
        emisor_map = {
            1: self.emisor1_id,
            2: self.emisor2_id,
            3: self.emisor3_id,
        }

        for idx, pid in emisor_map.items():
            if pid is None:
                return False
            if idx == 1 and not self.usuario1_aceptado:
                return False
            if idx == 2 and not self.usuario2_aceptado:
                return False
            if idx == 3 and not self.usuario3_aceptado:
                return False
        return True

    def todos_pares_confirmaron(self) -> bool:
        """Verifica si los 3 pares confirmaron el trueque múltiple."""
        return self.par1_confirmado and self.par2_confirmado and self.par3_confirmado

    def obtener_pares_del_usuario(self, usuario):
        """Retorna una lista de pares (1, 2, o 3) en los que participa el usuario."""
        uid = usuario.id if isinstance(usuario, Usuario) else usuario
        pares = []
        
        # Verificar participación en cada par
        if uid in (self.emisor1_id, self.receptor1_id):
            pares.append(1)
        if uid in (self.emisor2_id, self.receptor2_id):
            pares.append(2)
        if uid in (self.emisor3_id, self.receptor3_id):
            pares.append(3)
        
        return pares

class ResenaMultiple(models.Model):
    trueque_multiple = models.ForeignKey(AcuerdoTruequeMultiple, on_delete=models.CASCADE, related_name='resenas_multiple')
    calificador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='resenas_multiple_emitidas')
    calificado = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='resenas_multiple_recibidas')
    estrellas = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(max_length=500)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['trueque_multiple', 'calificador', 'calificado'], name='una_resena_multiple_por_calificador_por_calificado')]

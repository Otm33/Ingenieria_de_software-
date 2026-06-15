import uuid
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Case, IntegerField, Q, Value, When
from django.utils import timezone

VIGENCIA_SALDO_COMERCIAL_ANIOS = 12


class UsuarioAutorizadoQuerySet(models.QuerySet):
    def existe_email(self, email, tipo=None):
        queryset = self.filter(email=email)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        return queryset.exists()


class UsuarioAutorizadoManager(models.Manager):
    def get_queryset(self):
        return UsuarioAutorizadoQuerySet(self.model, using=self._db)

    def existe_email(self, email, tipo=None):
        return self.get_queryset().existe_email(email, tipo=tipo)

    def guardar_email(self, email, tipo="USUARIO"):
        return self.update_or_create(
            email=email,
            defaults={"tipo": tipo},
        )


class UsuarioAutorizado(models.Model):
    """HU1: Lista blanca de correos autorizados por el Administrador via CSV."""
    TIPO_CHOICES = [('USUARIO', 'Usuario'), ('COMERCIO', 'Comercio')]

    email = models.EmailField(unique=True)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='USUARIO')
    cargado_el = models.DateTimeField(auto_now_add=True)

    objects = UsuarioAutorizadoManager()

    def __str__(self):
        return f"{self.email} ({self.tipo})"


class UsuarioQuerySet(models.QuerySet):
    def comercios_activos(self):
        return list(self.filter(es_comercio=True, is_active=True))


class UsuarioManager(UserManager):
    def get_queryset(self):
        return UsuarioQuerySet(self.model, using=self._db)

    def existe_username(self, username):
        return self.filter(username=username).exists()

    def crear_usuario(self, username, email, password, nombre_real, es_comercio=False):
        return self.create_user(
            username=username,
            email=email,
            password=password,
            nombre_real=nombre_real,
            es_comercio=es_comercio,
        )

    def obtener_por_id(self, usuario_id):
        return self.get(id=usuario_id)

    def obtener_por_id_bloqueado(self, usuario_id):
        return self.select_for_update().get(id=usuario_id)

    def listar_comercios_activos(self):
        return self.get_queryset().comercios_activos()

    def guardar(self, usuario):
        usuario.save()
        return usuario

    def buscar_candidatos_match(self, usuario, titulos_necesidades, titulos_talentos):
        if not titulos_necesidades or not titulos_talentos:
            return self.none()

        return (
            self.filter(
                publicaciones__tipo="TALENTO",
                publicaciones__titulo__in=titulos_necesidades,
                publicaciones__esta_activa=True,
            )
            .filter(
                publicaciones__tipo="NECESIDAD",
                publicaciones__titulo__in=titulos_talentos,
                publicaciones__esta_activa=True,
            )
            .exclude(id=usuario.id)
            .distinct()
        )

    def buscar_candidatos_por_publicacion(self, usuario, publicacion):
        if not publicacion or not publicacion.titulo:
            return self.none()

        tipo_buscado = "NECESIDAD" if publicacion.tipo == "TALENTO" else "TALENTO"
        return (
            self.filter(
                publicaciones__tipo=tipo_buscado,
                publicaciones__titulo=publicacion.titulo,
                publicaciones__esta_activa=True,
            )
            .exclude(id=usuario.id)
            .distinct()
        )


class Usuario(AbstractUser):
    """HU2: Perfil del usuario con balance de Horas de Vida y reputación."""
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
    estado_social = models.CharField(max_length=15, choices=ESTADO_SOCIAL_CHOICES, default='NINGUNO')
    horas_recibidas_donacion = models.FloatField(default=0.0)
    es_fondo_comunitario = models.BooleanField(default=False)

    objects = UsuarioManager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(horas_de_vida__gte=-10.0),
                name="limite_balance_negativo_horas",
            ),
        ]

    @property
    def promedio_estrellas(self):
        resenas = self.resenas_recibidas.all()
        if not resenas:
            return 5.0
        return sum(r.estrellas for r in resenas) / resenas.count()

    def es_comercio_activo(self):
        """HU5: Verifica si es un comercio afiliado activo."""
        return self.es_comercio and self.is_active

    def puede_emitir_vuelto_comercial(self, monto):
        """HU5: Verifica si el comercio puede emitir vuelto comercial (deuda permitida)."""
        if not self.es_comercio_activo():
            return False, "Solo los comercios activos pueden emitir vuelto."
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


class PublicacionQuerySet(models.QuerySet):
    def activas(self):
        return self.filter(esta_activa=True)

    def por_usuario(self, usuario, solo_activas=False):
        queryset = self.filter(usuario=usuario)
        if solo_activas:
            queryset = queryset.filter(esta_activa=True)
        return list(queryset.order_by("-id"))

    def cartelera(self, categoria=None, urgencias=None):
        queryset = self.filter(esta_activa=True)
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        if urgencias:
            queryset = queryset.filter(urgencia__in=urgencias)
        return queryset.annotate(
            prioridad_urgencia=Case(
                When(urgencia="CRITICA", then=Value(3)),
                When(urgencia="ALTA", then=Value(2)),
                When(urgencia="NORMAL", then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
        ).order_by("-prioridad_urgencia", "-id")

    def titulos_activos_por_usuario_y_tipo(self, usuario, tipo):
        return list(
            self.filter(usuario=usuario, tipo=tipo, esta_activa=True)
            .values_list("titulo", flat=True)
            .distinct(),
        )

    def categorias_activas_por_usuario_y_tipo(self, usuario, tipo):
        return list(
            self.filter(usuario=usuario, tipo=tipo, esta_activa=True)
            .values_list("categoria", flat=True),
        )

    def coincidencias_complementarias(self, usuario, publicacion_seleccionada):
        if not publicacion_seleccionada or not publicacion_seleccionada.titulo:
            return self.none(), None

        tipo_buscado = "NECESIDAD" if publicacion_seleccionada.tipo == "TALENTO" else "TALENTO"
        queryset = self.filter(
            usuario=usuario,
            titulo=publicacion_seleccionada.titulo,
            tipo=tipo_buscado,
            esta_activa=True,
        )
        return queryset, tipo_buscado


class PublicacionManager(models.Manager):
    def get_queryset(self):
        return PublicacionQuerySet(self.model, using=self._db)

    def crear(self, usuario, datos):
        return self.create(usuario=usuario, **datos)

    def obtener_por_id(self, publicacion_id):
        return self.get(id=publicacion_id)

    def obtener_por_id_y_usuario(self, publicacion_id, usuario):
        return self.get(id=publicacion_id, usuario=usuario)

    def listar_por_usuario(self, usuario, solo_activas=False):
        return self.get_queryset().por_usuario(usuario, solo_activas=solo_activas)

    def contar_activas_por_tipo(self, usuario, tipo):
        return self.filter(usuario=usuario, tipo=tipo, esta_activa=True).count()

    def obtener_cartelera(self, categoria=None, urgencias=None):
        return self.get_queryset().cartelera(categoria=categoria, urgencias=urgencias)

    def titulos_activos_por_usuario_y_tipo(self, usuario, tipo):
        return self.get_queryset().titulos_activos_por_usuario_y_tipo(usuario, tipo)

    def categorias_activas_por_usuario_y_tipo(self, usuario, tipo):
        return self.get_queryset().categorias_activas_por_usuario_y_tipo(usuario, tipo)

    def verificar_coincidencia_por_titulo(self, usuario, publicacion_seleccionada):
        coincidencias, tipo_buscado = self.get_queryset().coincidencias_complementarias(
            usuario,
            publicacion_seleccionada,
        )
        if tipo_buscado is None:
            return {
                "tiene_coincidencia": False,
                "publicaciones_coincidentes": [],
                "tipo_buscado": None,
                "titulo": None,
            }

        publicaciones_coincidentes = list(coincidencias)
        return {
            "tiene_coincidencia": len(publicaciones_coincidentes) > 0,
            "publicaciones_coincidentes": publicaciones_coincidentes,
            "tipo_buscado": tipo_buscado,
            "titulo": publicacion_seleccionada.titulo,
        }


class Publicacion(models.Model):
    """HU2 y HU3: Catálogo de ofertas (Talentos) y demandas (Necesidades)."""
    TIPO_CHOICES = [('TALENTO', 'Talento'), ('NECESIDAD', 'Necesidad')]
    URGENCIA_CHOICES = [('NORMAL', 'Normal'), ('ALTA', 'Urgencia Alta'), ('CRITICA', 'Necesidad Crítica')]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='publicaciones')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=80, db_index=True)
    urgencia = models.CharField(max_length=10, choices=URGENCIA_CHOICES, default='NORMAL', db_index=True)
    esta_activa = models.BooleanField(default=True)
    es_causa_social = models.BooleanField(default=False, db_index=True)

    objects = PublicacionManager()

    def save(self, *args, **kwargs):
        if self.tipo == 'TALENTO' and self.esta_activa:
            conteo = Publicacion.objects.filter(usuario=self.usuario, tipo='TALENTO', esta_activa=True).count()
            if conteo >= 5 and not self.pk:
                raise ValidationError("No puedes tener más de 5 talentos activos publicados simultáneamente.")

        if self.tipo == 'NECESIDAD' and self.esta_activa and not self.es_causa_social:
            conteo = Publicacion.objects.filter(
                usuario=self.usuario,
                tipo='NECESIDAD',
                esta_activa=True,
                es_causa_social=False,
            ).count()
            if conteo >= 3 and not self.pk:
                raise ValidationError("No puedes tener más de 3 necesidades activas simultáneamente.")

        if self.usuario.horas_de_vida < -10.0:
            raise ValidationError("Saldo crítico inferior a -10 horas. Operación bloqueada.")

        if self.tipo == "TALENTO" and self.urgencia != "NORMAL":
            raise ValidationError("Los talentos solo pueden tener urgencia Normal.")

        super().save(*args, **kwargs)


class AcuerdoTruequeQuerySet(models.QuerySet):
    def por_usuario(self, usuario):
        return self.filter(
            Q(emisor=usuario) | Q(receptor=usuario),
        ).select_related(
            "emisor",
            "receptor",
            "publicacion_emisor",
            "publicacion_receptor",
        )


class AcuerdoTruequeManager(models.Manager):
    def get_queryset(self):
        return AcuerdoTruequeQuerySet(self.model, using=self._db)

    def crear(self, emisor, receptor, publicacion_emisor=None, publicacion_receptor=None):
        return self.create(
            emisor=emisor,
            receptor=receptor,
            publicacion_emisor=publicacion_emisor,
            publicacion_receptor=publicacion_receptor,
            estado="PENDIENTE",
        )

    def obtener_bloqueado(self, trueque_id):
        return self.select_for_update().get(id=trueque_id)

    def obtener_por_receptor(self, trueque_id, receptor):
        return self.get(id=trueque_id, receptor=receptor)

    def obtener_por_participante(self, trueque_id, usuario):
        return self.get(
            Q(id=trueque_id) & (Q(emisor=usuario) | Q(receptor=usuario)),
        )

    def listar_por_usuario(self, usuario):
        return self.get_queryset().por_usuario(usuario)

    def obtener_o_crear_pendiente(self, emisor, receptor, publicacion_emisor=None, publicacion_receptor=None):
        existente = self.filter(
            Q(emisor=emisor, receptor=receptor) | Q(emisor=receptor, receptor=emisor),
            estado="PENDIENTE",
        ).first()
        if existente:
            existente.emisor = emisor
            existente.receptor = receptor
            if publicacion_emisor is not None:
                existente.publicacion_emisor = publicacion_emisor
            if publicacion_receptor is not None:
                existente.publicacion_receptor = publicacion_receptor
            existente.save()
            return existente
        return self.crear(
            emisor=emisor,
            receptor=receptor,
            publicacion_emisor=publicacion_emisor,
            publicacion_receptor=publicacion_receptor,
        )

    def guardar(self, trueque):
        trueque.save()
        return trueque


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
    publicacion_emisor = models.ForeignKey(
        'Publicacion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trueques_como_emisor',
    )
    publicacion_receptor = models.ForeignKey(
        'Publicacion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='trueques_como_receptor',
    )
    emisor_confirmado = models.BooleanField(default=False)
    receptor_confirmado = models.BooleanField(default=False)
    creado_el = models.DateTimeField(auto_now_add=True, null=True)
    actualizado_el = models.DateTimeField(auto_now=True, null=True)

    objects = AcuerdoTruequeManager()


class ResenaQuerySet(models.QuerySet):
    def por_calificado(self, calificado):
        return list(self.filter(calificado=calificado))


class ResenaManager(models.Manager):
    def get_queryset(self):
        return ResenaQuerySet(self.model, using=self._db)

    def crear(self, trueque, calificador, calificado, estrellas, comentario):
        return self.create(
            trueque=trueque,
            calificador=calificador,
            calificado=calificado,
            estrellas=estrellas,
            comentario=comentario,
        )

    def listar_por_calificado(self, calificado):
        return self.get_queryset().por_calificado(calificado)


class Resena(models.Model):
    """HU4: Calificaciones e historial de confianza post-trueque."""
    trueque = models.ForeignKey(AcuerdoTrueque, on_delete=models.CASCADE, related_name='resenas')
    calificador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='resenas_emitidadas')
    calificado = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='resenas_recibidas')
    estrellas = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(max_length=500)

    objects = ResenaManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['trueque', 'calificador'],
                name='una_resena_por_usuario_por_trueque',
            ),
        ]


class NotificacionPropuestaQuerySet(models.QuerySet):
    def para_usuario(self, usuario, incluir_leidas=False):
        queryset = self.filter(destinatario=usuario)
        if not incluir_leidas:
            queryset = queryset.exclude(estado='LEIDA')
        return list(queryset.order_by('-prioridad', '-creada_el'))

    def existe_match_entre(self, usuario_a, usuario_b):
        return self.filter(
            tipo="MATCH",
            trueque__estado="PENDIENTE",
        ).filter(
            Q(destinatario=usuario_a, remitente=usuario_b)
            | Q(destinatario=usuario_b, remitente=usuario_a),
        ).exists()


class NotificacionPropuestaManager(models.Manager):
    def get_queryset(self):
        return NotificacionPropuestaQuerySet(self.model, using=self._db)

    def crear_notificacion(
        self,
        destinatario,
        remitente,
        trueque,
        publicacion_original,
        mensaje,
        tipo="PROPUESTA",
        match_detalle=None,
    ):
        return self.create(
            destinatario=destinatario,
            remitente=remitente,
            trueque=trueque,
            publicacion_original=publicacion_original,
            mensaje=mensaje,
            match_detalle=match_detalle,
            prioridad=True,
            estado="PENDIENTE",
            tipo=tipo,
        )

    def existe_match_entre(self, usuario_a, usuario_b):
        return self.get_queryset().existe_match_entre(usuario_a, usuario_b)

    def existe_match_pendiente_entre(self, usuario_a, usuario_b):
        return self.existe_match_entre(usuario_a, usuario_b)

    def actualizar_estado_por_trueque(self, trueque, nuevo_estado):
        return self.filter(
            trueque=trueque,
            tipo="PROPUESTA",
        ).update(estado=nuevo_estado)

    def obtener_notificaciones_usuario(self, usuario, incluir_leidas=False):
        return self.get_queryset().para_usuario(usuario, incluir_leidas=incluir_leidas)

    def marcar_como_leida(self, notificacion_id, destinatario=None):
        queryset = self.filter(id=notificacion_id)
        if destinatario is not None:
            queryset = queryset.filter(destinatario=destinatario)
        notificacion = queryset.get()
        notificacion.estado = 'LEIDA'
        notificacion.leida_el = timezone.now()
        notificacion.save()
        return notificacion

    def marcar_leidas_por_trueque(self, usuario, trueque_id, tipos=None):
        tipos = tipos or ("MATCH", "PROPUESTA")
        ahora = timezone.now()
        return self.filter(
            destinatario=usuario,
            trueque_id=trueque_id,
            tipo__in=tipos,
        ).exclude(estado="LEIDA").update(estado="LEIDA", leida_el=ahora)


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
    prioridad = models.BooleanField(default=True)

    objects = NotificacionPropuestaManager()

    class Meta:
        ordering = ['-prioridad', '-creada_el']


class SaldoComercialManager(models.Manager):
    def crear_movimiento(
        self,
        comercio,
        cliente,
        monto,
        tipo_movimiento,
        valor_producto=None,
        monto_recibido=None,
    ):
        fecha_expiracion = timezone.now() + timedelta(days=365 * VIGENCIA_SALDO_COMERCIAL_ANIOS)
        return self.create(
            comercio=comercio,
            cliente=cliente,
            monto_excedente=monto,
            tipo_movimiento=tipo_movimiento,
            fecha_expiracion=fecha_expiracion,
            valor_producto=valor_producto,
            monto_recibido=monto_recibido,
        )


class SaldoComercial(models.Model):
    TIPO_MOVIMIENTO = [
        ('EMISION', 'Emisión de vuelto'),
        ('PAGO', 'Pago en comercio'),
    ]
    comercio = models.ForeignKey(Usuario, related_name='operaciones_comerciales', on_delete=models.CASCADE)
    cliente = models.ForeignKey(Usuario, related_name='movimientos_saldo', on_delete=models.CASCADE)
    monto_excedente = models.DecimalField(max_digits=10, decimal_places=2)
    valor_producto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    monto_recibido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO, default='EMISION')
    fecha = models.DateTimeField(auto_now_add=True)
    # Vigencia documentada 12 años; la validación estricta en pagos queda fuera de esta fase.
    fecha_expiracion = models.DateTimeField()

    objects = SaldoComercialManager()


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

    def __str__(self):
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

    def __str__(self):
        return f"Donación {self.monto}h ({self.tipo_destino})"

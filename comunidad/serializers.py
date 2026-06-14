from rest_framework import serializers

from .models import AcuerdoTrueque, AcuerdoTruequeMultiple, NotificacionPropuesta, Publicacion, Resena, ResenaMultiple, SaldoComercial, Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    promedio_estrellas = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            "id",
            "username",
            "email",
            "nombre_real",
            "horas_de_vida",
            "promedio_estrellas",
            "es_comercio",
            "is_staff",
            "is_superuser",
        ]

    def get_promedio_estrellas(self, obj):
        return obj.promedio_estrellas


class PublicacionSerializer(serializers.ModelSerializer):
    usuario_nombre_real = serializers.CharField(source="usuario.nombre_real", read_only=True)
    usuario_estrellas = serializers.SerializerMethodField()

    class Meta:
        model = Publicacion
        fields = [
            "id",
            "usuario",
            "usuario_nombre_real",
            "usuario_estrellas",
            "tipo",
            "titulo",
            "descripcion",
            "categoria",
            "urgencia",
            "esta_activa",
        ]

    def get_usuario_estrellas(self, obj):
        return obj.usuario.promedio_estrellas


class AcuerdoTruequeSerializer(serializers.ModelSerializer):
    emisor_nombre = serializers.CharField(source="emisor.nombre_real", read_only=True)
    receptor_nombre = serializers.CharField(source="receptor.nombre_real", read_only=True)
    publicacion_emisor = PublicacionSerializer(read_only=True)
    publicacion_receptor = PublicacionSerializer(read_only=True)
    puede_confirmar = serializers.SerializerMethodField()
    pendiente_resena = serializers.SerializerMethodField()
    es_intercambio_mutuo = serializers.SerializerMethodField()
    impacto_horas = serializers.SerializerMethodField()
    oferta_propia_titulo = serializers.SerializerMethodField()
    oferta_contraparte_titulo = serializers.SerializerMethodField()

    class Meta:
        model = AcuerdoTrueque
        fields = [
            "id",
            "emisor",
            "receptor",
            "emisor_nombre",
            "receptor_nombre",
            "estado",
            "publicacion_emisor",
            "publicacion_receptor",
            "emisor_confirmado",
            "receptor_confirmado",
            "puede_confirmar",
            "pendiente_resena",
            "es_intercambio_mutuo",
            "impacto_horas",
            "oferta_propia_titulo",
            "oferta_contraparte_titulo",
            "codigo_confirmacion",
            "creado_el",
            "actualizado_el",
        ]

    def _trueque_service(self):
        from .services import TruequeService
        return TruequeService

    def get_es_intercambio_mutuo(self, obj):
        return self._trueque_service()._es_intercambio_mutuo(obj)

    def get_impacto_horas(self, obj):
        if self.get_es_intercambio_mutuo(obj):
            return 0
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return 1
        prestador, receptor_servicio = self._trueque_service()._identificar_roles_trueque(obj)
        if request.user == prestador:
            return 1
        if request.user == receptor_servicio:
            return -1
        return 0

    def get_oferta_propia_titulo(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        if self.get_es_intercambio_mutuo(obj):
            if request.user == obj.emisor and obj.publicacion_emisor:
                return obj.publicacion_emisor.titulo
            if request.user == obj.receptor and obj.publicacion_receptor:
                return obj.publicacion_receptor.titulo
            return None
        prestador, _ = self._trueque_service()._identificar_roles_trueque(obj)
        if request.user == prestador and obj.publicacion_emisor and obj.publicacion_emisor.tipo == "TALENTO":
            return obj.publicacion_emisor.titulo
        if request.user == obj.receptor and obj.publicacion_receptor and obj.publicacion_receptor.tipo == "TALENTO":
            return obj.publicacion_receptor.titulo
        if request.user == obj.emisor and obj.publicacion_emisor:
            return obj.publicacion_emisor.titulo
        if request.user == obj.receptor and obj.publicacion_receptor:
            return obj.publicacion_receptor.titulo
        return None

    def get_oferta_contraparte_titulo(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        if self.get_es_intercambio_mutuo(obj):
            if request.user == obj.emisor and obj.publicacion_receptor:
                return obj.publicacion_receptor.titulo
            if request.user == obj.receptor and obj.publicacion_emisor:
                return obj.publicacion_emisor.titulo
            return None
        prestador, receptor_servicio = self._trueque_service()._identificar_roles_trueque(obj)
        if request.user == receptor_servicio and obj.publicacion_emisor and obj.publicacion_emisor.tipo == "TALENTO":
            return obj.publicacion_emisor.titulo
        if request.user == prestador and obj.publicacion_receptor and obj.publicacion_receptor.tipo == "NECESIDAD":
            return obj.publicacion_receptor.titulo
        if request.user == obj.emisor and obj.publicacion_receptor:
            return obj.publicacion_receptor.titulo
        if request.user == obj.receptor and obj.publicacion_emisor:
            return obj.publicacion_emisor.titulo
        return None

    def get_puede_confirmar(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        if request.user not in [obj.emisor, obj.receptor]:
            return False
        if obj.estado != "ACEPTADO":
            return False
        if request.user == obj.emisor:
            return not obj.emisor_confirmado
        return not obj.receptor_confirmado

    def get_pendiente_resena(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        if obj.estado != "FINALIZADO":
            return False
        if request.user not in [obj.emisor, obj.receptor]:
            return False
        return not Resena.objects.filter(trueque=obj, calificador=request.user).exists()


class MatchEnriquecidoSerializer(serializers.Serializer):
    usuario = UsuarioSerializer()
    talentos_coincidentes = PublicacionSerializer(many=True)
    necesidades_coincidentes = PublicacionSerializer(many=True)
    publicaciones_sugeridas = serializers.ListField(child=serializers.DictField(), allow_empty=True)


class NotificacionSerializer(serializers.ModelSerializer):
    remitente_nombre = serializers.CharField(source="remitente.nombre_real", read_only=True)
    remitente_username = serializers.CharField(source="remitente.username", read_only=True)
    remitente_id = serializers.IntegerField(source="remitente.id", read_only=True)
    trueque_id = serializers.IntegerField(source="trueque.id", read_only=True)
    trueque_multiple_id = serializers.IntegerField(source="trueque_multiple.id", read_only=True)
    publicacion_titulo = serializers.CharField(source="publicacion_original.titulo", read_only=True)
    publicacion_tipo = serializers.CharField(source="publicacion_original.tipo", read_only=True)
    acciones = serializers.SerializerMethodField()

    class Meta:
        model = NotificacionPropuesta
        fields = [
            "id",
            "tipo",
            "mensaje",
            "match_detalle",
            "remitente_id",
            "remitente_nombre",
            "remitente_username",
            "trueque_id",
            "trueque_multiple_id",
            "estado",
            "publicacion_titulo",
            "publicacion_tipo",
            "acciones",
            "creada_el",
            "prioridad",
        ]

    def get_acciones(self, obj):
        acciones = ["marcar_leida"]
        if obj.tipo == "PROPUESTA" and obj.estado == "PENDIENTE":
            acciones.extend(["aceptar", "rechazar"])
        if obj.tipo == "MATCH" and obj.estado == "PENDIENTE":
            acciones.append("crear_propuesta")
        return acciones


class ResenaSerializer(serializers.ModelSerializer):
    calificador_username = serializers.CharField(source="calificador.username", read_only=True)
    calificador_nombre = serializers.CharField(source="calificador.nombre_real", read_only=True)

    class Meta:
        model = Resena
        fields = [
            "id",
            "trueque",
            "calificador",
            "calificador_username",
            "calificador_nombre",
            "calificado",
            "estrellas",
            "comentario",
        ]


class SaldoComercialSerializer(serializers.ModelSerializer):
    comercio_nombre = serializers.CharField(source="comercio.nombre_real", read_only=True)
    comercio_email = serializers.EmailField(source="comercio.email", read_only=True)
    cliente_nombre = serializers.CharField(source="cliente.nombre_real", read_only=True)
    cliente_email = serializers.EmailField(source="cliente.email", read_only=True)

    class Meta:
        model = SaldoComercial
        fields = [
            "id",
            "comercio",
            "comercio_nombre",
            "comercio_email",
            "cliente",
            "cliente_nombre",
            "cliente_email",
            "monto_excedente",
            "valor_producto",
            "monto_recibido",
            "tipo_movimiento",
            "fecha",
            "fecha_expiracion",
        ]


class AcuerdoTruequeMultipleSerializer(serializers.ModelSerializer):
    # Campos para los 3 pares
    emisor1_nombre = serializers.CharField(source='emisor1.nombre_real', read_only=True)
    receptor1_nombre = serializers.CharField(source='receptor1.nombre_real', read_only=True)
    emisor2_nombre = serializers.CharField(source='emisor2.nombre_real', read_only=True)
    receptor2_nombre = serializers.CharField(source='receptor2.nombre_real', read_only=True)
    emisor3_nombre = serializers.CharField(source='emisor3.nombre_real', read_only=True)
    receptor3_nombre = serializers.CharField(source='receptor3.nombre_real', read_only=True)
    
    # Publicaciones
    publicacion_emisor1 = PublicacionSerializer(read_only=True)
    publicacion_receptor1 = PublicacionSerializer(read_only=True)
    publicacion_emisor2 = PublicacionSerializer(read_only=True)
    publicacion_receptor2 = PublicacionSerializer(read_only=True)
    publicacion_emisor3 = PublicacionSerializer(read_only=True)
    publicacion_receptor3 = PublicacionSerializer(read_only=True)
    
    # Métodos
    puede_aceptar = serializers.SerializerMethodField()
    todos_aceptaron = serializers.SerializerMethodField()
    esta_expirado = serializers.SerializerMethodField()
    todos_pares_confirmaron = serializers.SerializerMethodField()
    
    class Meta:
        model = AcuerdoTruequeMultiple
        fields = [
            'id',
            'emisor1', 'receptor1', 'emisor1_nombre', 'receptor1_nombre',
            'emisor2', 'receptor2', 'emisor2_nombre', 'receptor2_nombre',
            'emisor3', 'receptor3', 'emisor3_nombre', 'receptor3_nombre',
            'publicacion_emisor1', 'publicacion_receptor1',
            'publicacion_emisor2', 'publicacion_receptor2',
            'publicacion_emisor3', 'publicacion_receptor3',
            'estado',
            'usuario1_aceptado', 'usuario2_aceptado', 'usuario3_aceptado',
            'par1_confirmado', 'par2_confirmado', 'par3_confirmado',
            'codigo_par1', 'codigo_par2', 'codigo_par3',
            'creado_el', 'actualizado_el', 'expira_el',
            'puede_aceptar', 'todos_aceptaron', 'esta_expirado', 'todos_pares_confirmaron',
        ]
    
    def get_puede_aceptar(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if not obj.participante(request.user):
            return False
        # Permitimos aceptar también si el trueque ya está en 'ACEPTADO' pero
        # aún hay participantes que no han marcado su aceptación (caso raro
        # consistente con correcciones retroactivas).
        if obj.estado not in ('PENDIENTE', 'ACEPTADO'):
            return False
        # Determinar el rol del usuario preferentemente por su posición de emisor
        # (cada emisor representa un participante único). Si el flag del rol
        # aún no está marcado, puede aceptar.
        rol = obj.obtener_usuario_por_rol(request.user)
        if rol == 1 and not obj.usuario1_aceptado:
            return True
        if rol == 2 and not obj.usuario2_aceptado:
            return True
        if rol == 3 and not obj.usuario3_aceptado:
            return True
        return False
    
    def get_todos_aceptaron(self, obj):
        return obj.todos_aceptaron()
    
    def get_esta_expirado(self, obj):
        return obj.esta_expirado()
    
    def get_todos_pares_confirmaron(self, obj):
        return obj.todos_pares_confirmaron()


class ResenaMultipleSerializer(serializers.ModelSerializer):
    calificador_nombre = serializers.CharField(source='calificador.nombre_real', read_only=True)
    calificado_nombre = serializers.CharField(source='calificado.nombre_real', read_only=True)
    
    class Meta:
        model = ResenaMultiple
        fields = [
            'id',
            'trueque_multiple',
            'calificador',
            'calificador_nombre',
            'calificado',
            'calificado_nombre',
            'estrellas',
            'comentario',
        ]

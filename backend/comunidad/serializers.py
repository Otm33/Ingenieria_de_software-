from rest_framework import serializers

from .models import AcuerdoTrueque, AcuerdoTruequeMultiple, NotificacionPropuesta, Publicacion, Resena, ResenaMultiple, SaldoComercial, Usuario, SolicitudApoyoSocial, DonacionHoras


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
            "saldo_comercial",
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
        # Solo en EN_CURSO (receptor aceptó, servicio en progreso)
        if obj.estado != "EN_CURSO":
            return False
        # Solo el receptor puede confirmar (el emisor solo comparte el código)
        if request.user == obj.emisor:
            return False
        return not obj.receptor_confirmado

    def get_pendiente_resena(self, obj):
        import logging
        logger = logging.getLogger(__name__)
        
        request = self.context.get("request")
        logger.info(f"pendiente_resena - trueque_id={obj.id}, estado={obj.estado}, request={request is not None}")
        
        if not request or not request.user.is_authenticated:
            logger.info("pendiente_resena - no request or not authenticated")
            return False
        
        # Reseñas pendientes solo en FINALIZADO (código validado)
        if obj.estado != "FINALIZADO":
            logger.info(f"pendiente_resena - estado no válido: {obj.estado}")
            return False
        
        # Comparar IDs en lugar de objetos
        user_id = request.user.id
        emisor_id = getattr(obj.emisor, 'id', obj.emisor) if hasattr(obj.emisor, 'id') else obj.emisor
        receptor_id = getattr(obj.receptor, 'id', obj.receptor) if hasattr(obj.receptor, 'id') else obj.receptor
        
        logger.info(f"pendiente_resena - user_id={user_id}, emisor_id={emisor_id}, receptor_id={receptor_id}")
        
        if user_id not in (emisor_id, receptor_id):
            logger.info("pendiente_resena - usuario no es participante")
            return False
        
        # Determinar la contraparte del usuario
        contraparte_id = receptor_id if user_id == emisor_id else emisor_id
        
        # Verificar si el usuario ya calificó a su contraparte específica
        tiene_resena = Resena.objects.filter(trueque=obj, calificador_id=user_id, calificado_id=contraparte_id).exists()
        logger.info(f"pendiente_resena - contraparte_id={contraparte_id}, tiene_resena={tiene_resena}, resultado={not tiene_resena}")
        
        return not tiene_resena


class PublicacionDominioSerializer(serializers.Serializer):
    """Serializa entidades PublicacionDominio (no ORM).
    Usa los campos desnormalizados poblados por el repositorio.
    """
    id = serializers.IntegerField()
    usuario = serializers.IntegerField(source='usuario_id')
    usuario_nombre_real = serializers.CharField()
    usuario_estrellas = serializers.FloatField(source='usuario_promedio_estrellas')
    tipo = serializers.CharField()
    titulo = serializers.CharField()
    descripcion = serializers.CharField()
    categoria = serializers.CharField()
    urgencia = serializers.CharField()
    esta_activa = serializers.BooleanField()


class MatchEnriquecidoSerializer(serializers.Serializer):
    usuario = UsuarioSerializer()
    talentos_coincidentes = PublicacionDominioSerializer(many=True)
    necesidades_coincidentes = PublicacionDominioSerializer(many=True)
    publicaciones_sugeridas = serializers.ListField(child=serializers.DictField(), allow_empty=True)


class NotificacionSerializer(serializers.ModelSerializer):
    remitente_nombre = serializers.CharField(source="remitente.nombre_real", read_only=True)
    remitente_username = serializers.CharField(source="remitente.username", read_only=True)
    remitente_id = serializers.IntegerField(source="remitente.id", read_only=True)
    trueque_id = serializers.SerializerMethodField()
    trueque_multiple_id = serializers.SerializerMethodField()
    publicacion_titulo = serializers.SerializerMethodField()
    publicacion_tipo = serializers.SerializerMethodField()
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
        if obj.tipo == "RESENA" and obj.estado == "PENDIENTE":
            acciones.append("dejar_resena")
        return acciones

    def get_trueque_id(self, obj):
        return obj.trueque_id

    def get_trueque_multiple_id(self, obj):
        return obj.trueque_multiple_id

    def get_publicacion_titulo(self, obj):
        return obj.publicacion_original.titulo if obj.publicacion_original else None

    def get_publicacion_tipo(self, obj):
        return obj.publicacion_original.tipo if obj.publicacion_original else None


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
    pendiente_resena = serializers.SerializerMethodField()
    
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
            'pendiente_resena',
        ]
    
    def get_puede_aceptar(self, obj):
        from .negocio.trueque_multiple import es_participante, obtener_rol
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if not es_participante(obj, request.user):
            return False
        if obj.estado not in ('PENDIENTE', 'ACEPTADO'):
            return False
        rol = obtener_rol(obj, request.user)
        if rol == 1 and not obj.usuario1_aceptado:
            return True
        if rol == 2 and not obj.usuario2_aceptado:
            return True
        if rol == 3 and not obj.usuario3_aceptado:
            return True
        return False
    
    def get_todos_aceptaron(self, obj):
        from .negocio.trueque_multiple import todos_aceptaron
        return todos_aceptaron(obj)
    
    def get_esta_expirado(self, obj):
        from .negocio.trueque_multiple import esta_expirado
        return esta_expirado(obj)
    
    def get_todos_pares_confirmaron(self, obj):
        from .negocio.trueque_multiple import todos_pares_confirmaron
        return todos_pares_confirmaron(obj)
    
    def get_pendiente_resena(self, obj):
        from .negocio.trueque_multiple import es_participante, obtener_pares_del_usuario
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        if obj.estado != 'FINALIZADO':
            return False
        if not es_participante(obj, request.user):
            return False
        
        # Obtener los pares en los que participa el usuario
        pares_usuario = obtener_pares_del_usuario(obj, request.user)
        
        # Para cada par, verificar si el usuario ya calificó a su contraparte
        from backend.comunidad.models import ResenaMultiple
        for par in pares_usuario:
            # Obtener contraparte del usuario en este par
            contraparte_id = None
            if par == 1:
                if obj.emisor1_id == request.user.id:
                    contraparte_id = obj.receptor1_id
                else:
                    contraparte_id = obj.emisor1_id
            elif par == 2:
                if obj.emisor2_id == request.user.id:
                    contraparte_id = obj.receptor2_id
                else:
                    contraparte_id = obj.emisor2_id
            elif par == 3:
                if obj.emisor3_id == request.user.id:
                    contraparte_id = obj.receptor3_id
                else:
                    contraparte_id = obj.emisor3_id
            
            # Si hay contraparte y no existe reseña, hay reseña pendiente
            if contraparte_id and contraparte_id != request.user.id:
                if not ResenaMultiple.objects.filter(
                    trueque_multiple=obj, 
                    calificador=request.user, 
                    calificado_id=contraparte_id
                ).exists():
                    return True
        
        return False


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


# ── Sprint 2 HU1: Impacto Social ─────────────────────────────────────────────

class SolicitudApoyoSocialSerializer(serializers.ModelSerializer):
    solicitante_nombre = serializers.CharField(source="solicitante.nombre_real", read_only=True)
    estado_social_solicitante = serializers.CharField(source="solicitante.estado_social", read_only=True)
    necesidad_activa = serializers.SerializerMethodField()

    class Meta:
        model = SolicitudApoyoSocial
        fields = [
            "id",
            "solicitante",
            "solicitante_nombre",
            "categoria",
            "titulo",
            "descripcion",
            "estado",
            "horas_recibidas",
            "horas_solidarias_disponibles",
            "horas_solidarias_utilizadas",
            "publicacion_id",
            "necesidad_activa",
            "estado_social_solicitante",
            "creado_el",
            "actualizado_el",
        ]
        read_only_fields = [
            "id", "solicitante", "estado", "horas_recibidas",
            "horas_solidarias_disponibles", "horas_solidarias_utilizadas",
            "publicacion_id", "necesidad_activa", "creado_el", "actualizado_el",
        ]

    def get_necesidad_activa(self, obj):
        if obj.publicacion_id is None:
            return False
        publicacion = getattr(obj, "publicacion", None)
        if publicacion is None:
            return False
        return publicacion.esta_activa


class DonacionHorasSerializer(serializers.ModelSerializer):
    donante_nombre = serializers.CharField(source="donante.nombre_real", read_only=True)
    receptor_nombre = serializers.CharField(source="receptor.nombre_real", read_only=True)

    class Meta:
        model = DonacionHoras
        fields = [
            "id",
            "donante",
            "donante_nombre",
            "receptor",
            "receptor_nombre",
            "solicitud",
            "monto",
            "tipo_destino",
            "fecha",
            "comprobante_id",
        ]


class UsuarioEstadoSocialSerializer(serializers.ModelSerializer):
    """Serializer simplificado para la vista de admin de impacto social."""

    class Meta:
        model = Usuario
        fields = [
            "id",
            "username",
            "nombre_real",
            "horas_de_vida",
            "estado_social",
            "horas_recibidas_donacion",
        ]

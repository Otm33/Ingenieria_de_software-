from django.db.models import Case, IntegerField, Value, When

from .models import AcuerdoTrueque, NotificacionPropuesta, Publicacion, Resena, SaldoComercial, Usuario, UsuarioAutorizado


class UsuarioAutorizadoRepository:
    def existe_email(self, email, tipo=None):
        queryset = UsuarioAutorizado.objects.filter(email=email)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        return queryset.exists()

    def guardar_email(self, email, tipo="USUARIO"):
        autorizado, creado = UsuarioAutorizado.objects.update_or_create(
            email=email,
            defaults={"tipo": tipo},
        )
        return autorizado, creado


class UsuarioRepository:
    def existe_username(self, username):
        return Usuario.objects.filter(username=username).exists()

    def crear_usuario(self, username, email, password, nombre_real, es_comercio=False):
        return Usuario.objects.create_user(
            username=username,
            email=email,
            password=password,
            nombre_real=nombre_real,
            es_comercio=es_comercio,
        )

    def obtener_por_id(self, usuario_id):
        return Usuario.objects.get(id=usuario_id)

    def obtener_por_id_bloqueado(self, usuario_id):
        return Usuario.objects.select_for_update().get(id=usuario_id)

    def listar_comercios_activos(self):
        return list(Usuario.objects.filter(es_comercio=True, is_active=True))

    def guardar(self, usuario):
        usuario.save()
        return usuario


class PublicacionRepository:
    def crear(self, usuario, datos):
        return Publicacion.objects.create(usuario=usuario, **datos)

    def obtener_por_id(self, publicacion_id):
        return Publicacion.objects.get(id=publicacion_id)

    def obtener_por_id_y_usuario(self, publicacion_id, usuario):
        return Publicacion.objects.get(id=publicacion_id, usuario=usuario)

    def listar_por_usuario(self, usuario, solo_activas=False):
        queryset = Publicacion.objects.filter(usuario=usuario)
        if solo_activas:
            queryset = queryset.filter(esta_activa=True)
        return list(queryset.order_by("-id"))

    def contar_activas_por_tipo(self, usuario, tipo):
        return Publicacion.objects.filter(usuario=usuario, tipo=tipo, esta_activa=True).count()

    def obtener_cartelera(self, categoria=None, urgencias=None):
        queryset = Publicacion.objects.filter(esta_activa=True)

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
            prioridad_estrellas=Case(
                When(usuario__promedio_estrellas__lt=3.0, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
        ).order_by("-prioridad_estrellas", "-prioridad_urgencia", "-id")

    def categorias_activas_por_usuario_y_tipo(self, usuario, tipo):
        return list(
            Publicacion.objects.filter(usuario=usuario, tipo=tipo, esta_activa=True)
            .values_list("categoria", flat=True)
        )


class AcuerdoTruequeRepository:
    def crear(self, emisor, receptor, publicacion_emisor=None, publicacion_receptor=None):
        return AcuerdoTrueque.objects.create(
            emisor=emisor,
            receptor=receptor,
            publicacion_emisor=publicacion_emisor,
            publicacion_receptor=publicacion_receptor,
            estado="PENDIENTE",
        )

    def obtener_bloqueado(self, trueque_id):
        return AcuerdoTrueque.objects.select_for_update().get(id=trueque_id)

    def obtener_por_receptor(self, trueque_id, receptor):
        return AcuerdoTrueque.objects.get(id=trueque_id, receptor=receptor)

    def guardar(self, trueque):
        trueque.save()
        return trueque


class ResenaRepository:
    def crear(self, trueque, calificador, calificado, estrellas, comentario):
        return Resena.objects.create(
            trueque=trueque,
            calificador=calificador,
            calificado=calificado,
            estrellas=estrellas,
            comentario=comentario,
        )

    def listar_por_calificado(self, calificado):
        return list(Resena.objects.filter(calificado=calificado))


class SaldoComercialRepository:
    def crear_movimiento(self, comercio, cliente, monto, tipo_movimiento):
        return SaldoComercial.objects.create(
            comercio=comercio,
            cliente=cliente,
            monto_excedente=monto,
            tipo_movimiento=tipo_movimiento,
        )


class NotificacionPropuestaRepository:
    def crear_notificacion(self, destinatario, remitente, trueque, publicacion_original, mensaje):
        from .models import NotificacionPropuesta
        return NotificacionPropuesta.objects.create(
            destinatario=destinatario,
            remitente=remitente,
            trueque=trueque,
            publicacion_original=publicacion_original,
            mensaje=mensaje,
            prioridad=True,
            estado='PENDIENTE'
        )
    
    def obtener_notificaciones_usuario(self, usuario):
        from .models import NotificacionPropuesta
        return list(
            NotificacionPropuesta.objects.filter(destinatario=usuario)
            .exclude(estado='LEIDA')
            .order_by('-prioridad', '-creada_el')
        )
    
    def marcar_como_leida(self, notificacion_id):
        from .models import NotificacionPropuesta
        from django.utils import timezone
        notificacion = NotificacionPropuesta.objects.get(id=notificacion_id)
        notificacion.estado = 'LEIDA'
        notificacion.leida_el = timezone.now()
        notificacion.save()
        return notificacion


class MatchmakingRepository:
    def buscar_matches(self, usuario, categorias_necesarias, categorias_ofrecidas):
        if not categorias_necesarias or not categorias_ofrecidas:
            return []

        return list(
            Usuario.objects.filter(
                publicaciones__tipo="TALENTO",
                publicaciones__categoria__in=categorias_necesarias,
                publicaciones__esta_activa=True,
            )
            .filter(
                publicaciones__tipo="NECESIDAD",
                publicaciones__categoria__in=categorias_ofrecidas,
                publicaciones__esta_activa=True,
            )
            .exclude(id=usuario.id)
            .distinct()
        )
    
    def verificar_coincidencia_por_titulo(self, usuario, publicacion_seleccionada):
        """
        Verifica si el usuario tiene publicaciones con el mismo título que la publicación seleccionada.
        Retorna un diccionario con información sobre las coincidencias.
        """
        if not publicacion_seleccionada or not publicacion_seleccionada.titulo:
            return {
                "tiene_coincidencia": False,
                "publicaciones_coincidentes": [],
                "tipo_buscado": None,
                "titulo": None
            }
        
        # Determinar qué tipo de publicación buscamos (el complementario)
        tipo_buscado = "NECESIDAD" if publicacion_seleccionada.tipo == "TALENTO" else "TALENTO"
        
        # Buscar publicaciones del usuario con el mismo título y tipo complementario
        publicaciones_coincidentes = list(
            Publicacion.objects.filter(
                usuario=usuario,
                titulo=publicacion_seleccionada.titulo,
                tipo=tipo_buscado,
                esta_activa=True,
            )
        )
        
        return {
            "tiene_coincidencia": len(publicaciones_coincidentes) > 0,
            "publicaciones_coincidentes": publicaciones_coincidentes,
            "tipo_buscado": tipo_buscado,
            "titulo": publicacion_seleccionada.titulo
        }
    
    def buscar_matches_por_publicacion(self, usuario, publicacion):
        """
        Busca usuarios que tengan ofertas complementarias a una publicación específica.
        Si la publicación es un TALENTO, busca usuarios que tengan NECESIDADES en esa categoría.
        Si la publicación es una NECESIDAD, busca usuarios que tengan TALENTOS en esa categoría.
        """
        if not publicacion or not publicacion.categoria:
            return []
        
        tipo_buscado = "NECESIDAD" if publicacion.tipo == "TALENTO" else "TALENTO"
        
        # Buscar usuarios que tengan publicaciones del tipo complementario en la misma categoría
        usuarios_con_match = list(
            Usuario.objects.filter(
                publicaciones__tipo=tipo_buscado,
                publicaciones__categoria=publicacion.categoria,
                publicaciones__esta_activa=True,
            )
            .exclude(id=usuario.id)
            .distinct()
        )
        
        return usuarios_con_match

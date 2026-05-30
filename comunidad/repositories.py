from django.db.models import Case, IntegerField, Value, When

from .models import AcuerdoTrueque, Publicacion, Resena, SaldoComercial, Usuario, UsuarioAutorizado


class UsuarioAutorizadoRepository:
    def existe_email(self, email):
        return UsuarioAutorizado.objects.filter(email=email).exists()

    def guardar_email(self, email):
        return UsuarioAutorizado.objects.get_or_create(email=email)


class UsuarioRepository:
    def existe_username(self, username):
        return Usuario.objects.filter(username=username).exists()

    def crear_usuario(self, username, email, password, nombre_real):
        return Usuario.objects.create_user(
            username=username,
            email=email,
            password=password,
            nombre_real=nombre_real,
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
    def obtener_cartelera(self, categoria=None, urgencia=None):
        queryset = Publicacion.objects.filter(esta_activa=True)

        if categoria:
            queryset = queryset.filter(categoria=categoria)
        if urgencia:
            queryset = queryset.filter(urgencia=urgencia)

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
    def crear(self, emisor, receptor):
        return AcuerdoTrueque.objects.create(
            emisor=emisor,
            receptor=receptor,
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

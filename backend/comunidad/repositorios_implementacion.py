from typing import List, Optional

from django.db import transaction
from django.contrib.auth.hashers import make_password
from django.core.cache import cache

from .dominio.entidades import (
    AcuerdoTruequeDominio,
    NotificacionDominio,
    PublicacionDominio,
    ResenaDominio,
    UsuarioDominio,
    UsuarioAutorizadoDominio,
    ResenaMultipleDominio,
    SolicitudApoyoSocialDominio,
    DonacionHorasDominio,
)
from .interfaces.repository_interfaces import (
    INotificacionRepository,
    IPublicacionRepository,
    IResenaRepository,
    ITruequeRepository,
    IUsuarioRepository,
)


# ── Usuario ───────────────────────────────────────────────────────────────────

class UsuarioRepository(IUsuarioRepository):
    """
    Implementación del repositorio de Usuarios usando Django ORM.
    Mapea entre UsuarioDominio (RAM) y UsuarioORM (BD).
    """

    def _modelo_a_dominio(self, modelo) -> UsuarioDominio:
        from backend.comunidad.models import Usuario as UsuarioORM
        return UsuarioDominio(
            id=modelo.id,
            username=modelo.username,
            email=modelo.email,
            nombre_real=modelo.nombre_real,
            horas_de_vida=float(modelo.horas_de_vida),
            es_comercio=modelo.es_comercio,
            saldo_comercial=float(modelo.saldo_comercial),
            is_active=modelo.is_active,
            is_staff=modelo.is_staff,
            is_superuser=modelo.is_superuser,
            promedio_estrellas=float(modelo.promedio_estrellas or 0.0),
            # Sprint 2 HU1: Impacto Social
            estado_social=getattr(modelo, 'estado_social', 'NINGUNO'),
            horas_recibidas_donacion=float(getattr(modelo, 'horas_recibidas_donacion', 0.0)),
            es_fondo_comunitario=getattr(modelo, 'es_fondo_comunitario', False),
        )

    def existe_username(self, username: str) -> bool:
        from backend.comunidad.models import Usuario as UsuarioORM
        return UsuarioORM.objects.filter(username=username).exists()

    def obtener_por_id_bloqueado(self, usuario_id: int) -> Optional[UsuarioDominio]:
        from backend.comunidad.models import Usuario as UsuarioORM
        try:
            return self._modelo_a_dominio(UsuarioORM.objects.select_for_update().get(id=usuario_id))
        except UsuarioORM.DoesNotExist:
            return None

    def listar_no_comercios(self) -> List[UsuarioDominio]:
        from backend.comunidad.models import Usuario as UsuarioORM
        return [
            self._modelo_a_dominio(u)
            for u in UsuarioORM.objects.filter(
                es_comercio=False,
                is_active=True,
                is_staff=False,
                is_superuser=False,
            ).order_by('nombre_real', 'username')
        ]

    @transaction.atomic
    def crear_usuario(self, username: str, email: str, password: str, nombre_real: str, es_comercio: bool = False) -> UsuarioDominio:
        from backend.comunidad.models import Usuario as UsuarioORM
        modelo = UsuarioORM.objects.create_user(
            username=username,
            email=email,
            password=password,
            nombre_real=nombre_real,
            es_comercio=es_comercio,
        )
        return self._modelo_a_dominio(modelo)

    def obtener_por_id(self, usuario_id: int) -> Optional[UsuarioDominio]:
        from backend.comunidad.models import Usuario as UsuarioORM
        try:
            return self._modelo_a_dominio(UsuarioORM.objects.get(id=usuario_id))
        except UsuarioORM.DoesNotExist:
            return None

    def obtener_por_email(self, email: str) -> Optional[UsuarioDominio]:
        from backend.comunidad.models import Usuario as UsuarioORM
        try:
            return self._modelo_a_dominio(UsuarioORM.objects.get(email=email))
        except UsuarioORM.DoesNotExist:
            return None

    def obtener_por_username(self, username: str) -> Optional[UsuarioDominio]:
        from backend.comunidad.models import Usuario as UsuarioORM
        try:
            return self._modelo_a_dominio(UsuarioORM.objects.get(username=username))
        except UsuarioORM.DoesNotExist:
            return None

    def listar_activos(self) -> List[UsuarioDominio]:
        cache_key = 'usuarios_activos'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        from backend.comunidad.models import Usuario as UsuarioORM
        result = [
            self._modelo_a_dominio(u)
            for u in UsuarioORM.objects.filter(
                is_active=True, is_staff=False, is_superuser=False
            ).order_by("nombre_real", "username")
        ]
        cache.set(cache_key, result, timeout=300)  # 5 minutos
        return result

    def listar_comercios_activos(self) -> List[UsuarioDominio]:
        cache_key = 'comercios_activos'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        from backend.comunidad.models import Usuario as UsuarioORM
        result = [
            self._modelo_a_dominio(u)
            for u in UsuarioORM.objects.filter(es_comercio=True, is_active=True)
        ]
        cache.set(cache_key, result, timeout=300)  # 5 minutos
        return result

    @transaction.atomic
    def guardar(self, usuario_dominio: UsuarioDominio, password: str = None) -> UsuarioDominio:
        from backend.comunidad.models import Usuario as UsuarioORM
        if usuario_dominio.id:
            modelo = UsuarioORM.objects.get(id=usuario_dominio.id)
            modelo.username = usuario_dominio.username
            modelo.email = usuario_dominio.email
            modelo.nombre_real = usuario_dominio.nombre_real
            modelo.horas_de_vida = usuario_dominio.horas_de_vida
            modelo.es_comercio = usuario_dominio.es_comercio
            modelo.saldo_comercial = usuario_dominio.saldo_comercial
            modelo.is_active = usuario_dominio.is_active
            modelo.is_staff = getattr(usuario_dominio, 'is_staff', False)
            modelo.is_superuser = getattr(usuario_dominio, 'is_superuser', False)
            if password:
                modelo.password = make_password(password)
            modelo.save()
        else:
            modelo = UsuarioORM(
                username=usuario_dominio.username,
                email=usuario_dominio.email,
                nombre_real=usuario_dominio.nombre_real,
                horas_de_vida=usuario_dominio.horas_de_vida,
                es_comercio=usuario_dominio.es_comercio,
                saldo_comercial=usuario_dominio.saldo_comercial,
                is_active=usuario_dominio.is_active,
                is_staff=getattr(usuario_dominio, 'is_staff', False),
                is_superuser=getattr(usuario_dominio, 'is_superuser', False),
            )
            if password:
                modelo.password = make_password(password)
            modelo.save()
            usuario_dominio.id = modelo.id
        # Invalidar caché de usuarios
        cache.delete('usuarios_activos')
        cache.delete('comercios_activos')
        return usuario_dominio

    # ── Admin Panel (Sprint 2 HU3) ──

    def listar_todos(self, busqueda=None):
        from django.db.models import Q
        from backend.comunidad.models import Usuario as UsuarioORM
        qs = UsuarioORM.objects.all().order_by('-id')
        if busqueda:
            qs = qs.filter(
                Q(username__icontains=busqueda) |
                Q(email__icontains=busqueda) |
                Q(nombre_real__icontains=busqueda)
            )
        return [self._modelo_a_dominio(u) for u in qs]

    @transaction.atomic
    def actualizar_estado(self, usuario_id, is_active):
        from backend.comunidad.models import Usuario as UsuarioORM
        modelo = UsuarioORM.objects.get(id=usuario_id)
        modelo.is_active = is_active
        modelo.save()
        cache.delete('usuarios_activos')
        cache.delete('comercios_activos')
        return self._modelo_a_dominio(modelo)

    @transaction.atomic
    def actualizar_rol(self, usuario_id, is_staff):
        from backend.comunidad.models import Usuario as UsuarioORM
        modelo = UsuarioORM.objects.get(id=usuario_id)
        modelo.is_staff = is_staff
        modelo.save()
        return self._modelo_a_dominio(modelo)

    @transaction.atomic
    def eliminar(self, usuario_id):
        from backend.comunidad.models import Usuario as UsuarioORM
        UsuarioORM.objects.filter(id=usuario_id).delete()
        cache.delete('usuarios_activos')
        cache.delete('comercios_activos')

    def contar_estadisticas(self):
        from backend.comunidad.models import Usuario as UsuarioORM
        total = UsuarioORM.objects.count()
        activos = UsuarioORM.objects.filter(is_active=True).count()
        comercios = UsuarioORM.objects.filter(es_comercio=True).count()
        staff = UsuarioORM.objects.filter(is_staff=True).count()
        return {
            'total': total,
            'activos': activos,
            'comercios': comercios,
            'staff': staff,
        }


# ── Publicación ───────────────────────────────────────────────────────────────

class PublicacionRepository(IPublicacionRepository):
    """
    Implementación del repositorio de Publicaciones usando Django ORM.
    """

    def _modelo_a_dominio(self, modelo) -> PublicacionDominio:
        usuario = getattr(modelo, 'usuario', None)
        return PublicacionDominio(
            id=modelo.id,
            usuario_id=modelo.usuario_id,
            tipo=modelo.tipo,
            titulo=modelo.titulo,
            descripcion=modelo.descripcion,
            categoria=modelo.categoria,
            urgencia=modelo.urgencia,
            esta_activa=modelo.esta_activa,
            es_causa_social=getattr(modelo, 'es_causa_social', False),
            fecha_creacion=getattr(modelo, 'fecha_creacion', None),
            usuario_nombre_real=getattr(usuario, 'nombre_real', '') or '',
            usuario_promedio_estrellas=float(getattr(usuario, 'promedio_estrellas', 0.0) or 0.0),
            usuario_username=getattr(usuario, 'username', '') or '',
            usuario_is_active=getattr(usuario, 'is_active', True),
            usuario_horas_de_vida=float(getattr(usuario, 'horas_de_vida', 0.0) or 0.0),
        )

    def obtener_por_id(self, publicacion_id: int) -> Optional[PublicacionDominio]:
        from backend.comunidad.models import Publicacion as PublicacionORM
        try:
            return self._modelo_a_dominio(PublicacionORM.objects.get(id=publicacion_id))
        except PublicacionORM.DoesNotExist:
            return None

    def obtener_por_id_y_usuario(self, publicacion_id: int, usuario_id: int) -> Optional[PublicacionDominio]:
        from backend.comunidad.models import Publicacion as PublicacionORM
        try:
            return self._modelo_a_dominio(PublicacionORM.objects.get(id=publicacion_id, usuario_id=usuario_id))
        except PublicacionORM.DoesNotExist:
            return None

    def obtener_por_id_activa(self, publicacion_id: int) -> Optional[PublicacionDominio]:
        from backend.comunidad.models import Publicacion as PublicacionORM
        try:
            return self._modelo_a_dominio(PublicacionORM.objects.get(id=publicacion_id, esta_activa=True))
        except PublicacionORM.DoesNotExist:
            return None

    def obtener_todas_activas(self) -> List[PublicacionDominio]:
        from backend.comunidad.models import Publicacion as PublicacionORM
        return [
            self._modelo_a_dominio(p)
            for p in PublicacionORM.objects.filter(esta_activa=True).select_related('usuario')
        ]

    def listar_por_usuario_y_tipo_activas(self, usuario_id: int, tipo: str) -> List[PublicacionDominio]:
        from backend.comunidad.models import Publicacion as PublicacionORM
        return [
            self._modelo_a_dominio(p)
            for p in PublicacionORM.objects.filter(usuario_id=usuario_id, tipo=tipo, esta_activa=True)
        ]

    def titulos_activos_por_usuario_y_tipo(self, usuario_id: int, tipo: str) -> List[str]:
        from backend.comunidad.models import Publicacion as PublicacionORM
        return list(
            PublicacionORM.objects.filter(usuario_id=usuario_id, tipo=tipo, esta_activa=True)
            .values_list("titulo", flat=True)
            .distinct()
        )

    def categorias_activas_por_usuario_y_tipo(self, usuario_id: int, tipo: str) -> List[str]:
        from backend.comunidad.models import Publicacion as PublicacionORM
        return list(
            PublicacionORM.objects.filter(usuario_id=usuario_id, tipo=tipo, esta_activa=True)
            .values_list("categoria", flat=True)
        )

    def actualizar_estado(self, publicacion_id: int, usuario_id: int, esta_activa: bool) -> int:
        from backend.comunidad.models import Publicacion as PublicacionORM
        # Invalidar caché de publicaciones
        cache.delete_many([f'cartelera_{cat or "all"}_{"_".join(urg or ["all"])}' 
                          for cat in [None] 
                          for urg in [None, ['NORMAL'], ['ALTA'], ['CRITICA'], ['NORMAL', 'ALTA', 'CRITICA']]])
        return PublicacionORM.objects.filter(id=publicacion_id, usuario_id=usuario_id).update(esta_activa=esta_activa)

    @transaction.atomic
    def crear(self, usuario_id: int, datos: dict) -> PublicacionDominio:
        from backend.comunidad.models import Publicacion as PublicacionORM
        publicacion = PublicacionORM.objects.create(usuario_id=usuario_id, **datos)
        # Invalidar caché de publicaciones
        cache.delete_many([f'cartelera_{cat or "all"}_{"_".join(urg or ["all"])}'
                          for cat in [None, datos.get('categoria')]
                          for urg in [None, ['NORMAL'], ['ALTA'], ['CRITICA'], ['NORMAL', 'ALTA', 'CRITICA']]])
        return self._modelo_a_dominio(publicacion)

    @transaction.atomic
    def crear_causa_social(self, usuario_id: int, titulo: str, descripcion: str, categoria: str):
        """Sprint 2 HU1: Crea una publicación de NECESIDAD marcada como causa social.
        Retorna el ORM directamente (no aplica límites de publicaciones normales).
        """
        from backend.comunidad.models import Publicacion as PublicacionORM
        publicacion = PublicacionORM.objects.create(
            usuario_id=usuario_id,
            tipo="NECESIDAD",
            titulo=titulo,
            descripcion=descripcion,
            categoria=categoria,
            urgencia="ALTA",
            es_causa_social=True,
            esta_activa=True,
        )
        return publicacion

    def contar_activas_por_tipo(self, usuario_id: int, tipo: str) -> int:
        from backend.comunidad.models import Publicacion as PublicacionORM
        return PublicacionORM.objects.filter(
            usuario_id=usuario_id, tipo=tipo, esta_activa=True
        ).count()

    def listar_por_usuario(
        self, usuario_id: int, solo_activas: bool = False
    ) -> List[PublicacionDominio]:
        from backend.comunidad.models import Publicacion as PublicacionORM
        qs = PublicacionORM.objects.filter(usuario_id=usuario_id)
        if solo_activas:
            qs = qs.filter(esta_activa=True)
        return [self._modelo_a_dominio(p) for p in qs.order_by("-id")]

    def obtener_cartelera(
        self,
        categoria: Optional[str] = None,
        urgencias: Optional[List[str]] = None,
    ) -> List[PublicacionDominio]:
        # Generar clave de caché basada en los parámetros
        cache_key = f'cartelera_{categoria or "all"}_{"_".join(urgencias or ["all"])}'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        from django.db.models import Case, IntegerField, Value, When
        from backend.comunidad.models import Publicacion as PublicacionORM

        qs = PublicacionORM.objects.select_related('usuario').filter(esta_activa=True)
        if categoria:
            qs = qs.filter(categoria=categoria)
        if urgencias:
            qs = qs.filter(urgencia__in=urgencias)

        qs = qs.annotate(
            prioridad_urgencia=Case(
                When(urgencia="CRITICA", then=Value(3)),
                When(urgencia="ALTA", then=Value(2)),
                When(urgencia="NORMAL", then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by("-prioridad_urgencia", "-id")
        result = [self._modelo_a_dominio(p) for p in qs]
        cache.set(cache_key, result, timeout=300)  # 5 minutos
        return result

    @transaction.atomic
    def guardar(self, publicacion_dominio: PublicacionDominio) -> PublicacionDominio:
        from backend.comunidad.models import Publicacion as PublicacionORM
        if publicacion_dominio.id:
            modelo = PublicacionORM.objects.get(id=publicacion_dominio.id)
            modelo.usuario_id = publicacion_dominio.usuario_id
            modelo.tipo = publicacion_dominio.tipo
            modelo.titulo = publicacion_dominio.titulo
            modelo.descripcion = publicacion_dominio.descripcion
            modelo.categoria = publicacion_dominio.categoria
            modelo.urgencia = publicacion_dominio.urgencia
            modelo.esta_activa = publicacion_dominio.esta_activa
            # Guardado directo sin pasar por el save() de negocio del modelo
            PublicacionORM.objects.filter(id=modelo.id).update(
                tipo=modelo.tipo,
                titulo=modelo.titulo,
                descripcion=modelo.descripcion,
                categoria=modelo.categoria,
                urgencia=modelo.urgencia,
                esta_activa=modelo.esta_activa,
            )
        else:
            modelo = PublicacionORM(
                usuario_id=publicacion_dominio.usuario_id,
                tipo=publicacion_dominio.tipo,
                titulo=publicacion_dominio.titulo,
                descripcion=publicacion_dominio.descripcion,
                categoria=publicacion_dominio.categoria,
                urgencia=publicacion_dominio.urgencia,
                esta_activa=publicacion_dominio.esta_activa,
            )
            # Usar update_or_create o save bypassing validación del modelo ORM
            PublicacionORM.objects.bulk_create([modelo])
            publicacion_dominio.id = PublicacionORM.objects.filter(
                usuario_id=publicacion_dominio.usuario_id,
                titulo=publicacion_dominio.titulo,
            ).order_by("-id").first().id
        return publicacion_dominio

    # ── Admin Panel (Sprint 2 HU3) ──

    def listar_todas(self, busqueda=None):
        from django.db.models import Q
        from backend.comunidad.models import Publicacion as PublicacionORM
        qs = PublicacionORM.objects.select_related('usuario').order_by('-id')
        if busqueda:
            qs = qs.filter(
                Q(titulo__icontains=busqueda) |
                Q(descripcion__icontains=busqueda) |
                Q(categoria__icontains=busqueda) |
                Q(usuario__username__icontains=busqueda)
            )
        return [self._modelo_a_dominio(p) for p in qs]

    @transaction.atomic
    def eliminar(self, publicacion_id):
        from backend.comunidad.models import Publicacion as PublicacionORM
        PublicacionORM.objects.filter(id=publicacion_id).delete()

    @transaction.atomic
    def actualizar_estado_admin(self, publicacion_id, esta_activa):
        from backend.comunidad.models import Publicacion as PublicacionORM
        modelo = PublicacionORM.objects.get(id=publicacion_id)
        modelo.esta_activa = esta_activa
        modelo.save()
        return self._modelo_a_dominio(modelo)


# ── Trueque ───────────────────────────────────────────────────────────────────

class TruequeRepository(ITruequeRepository):
    """
    Implementación del repositorio de AcuerdoTrueque usando Django ORM.
    Nota: para lógica compleja de trueques, los controladores siguen delegando
    en TruequeService (que usa el viejo repositories.py). Este repositorio
    sirve para consultas simples de la capa de controladores delgados.
    """

    def _modelo_a_dominio(self, modelo) -> AcuerdoTruequeDominio:
        return AcuerdoTruequeDominio(
            id=modelo.id,
            emisor_id=modelo.emisor_id,
            receptor_id=modelo.receptor_id,
            estado=modelo.estado,
            publicacion_emisor_id=modelo.publicacion_emisor_id,
            publicacion_receptor_id=modelo.publicacion_receptor_id,
            emisor_confirmado=modelo.emisor_confirmado,
            receptor_confirmado=modelo.receptor_confirmado,
            codigo_confirmacion=modelo.codigo_confirmacion,
        )

    def obtener_por_id(self, trueque_id: int) -> Optional[AcuerdoTruequeDominio]:
        from backend.comunidad.models import AcuerdoTrueque as TruequeORM
        try:
            return self._modelo_a_dominio(TruequeORM.objects.get(id=trueque_id))
        except TruequeORM.DoesNotExist:
            return None

    def existe_codigo_confirmacion(self, codigo: str) -> bool:
        from backend.comunidad.models import AcuerdoTrueque as TruequeORM
        return TruequeORM.objects.filter(codigo_confirmacion=codigo).exists()

    def obtener_bloqueado(self, trueque_id: int) -> Optional[AcuerdoTruequeDominio]:
        from backend.comunidad.models import AcuerdoTrueque as TruequeORM
        try:
            return self._modelo_a_dominio(TruequeORM.objects.select_for_update().get(id=trueque_id))
        except TruequeORM.DoesNotExist:
            return None

    def obtener_por_receptor(self, trueque_id: int, receptor_id: int) -> Optional[AcuerdoTruequeDominio]:
        from backend.comunidad.models import AcuerdoTrueque as TruequeORM
        try:
            return self._modelo_a_dominio(TruequeORM.objects.get(id=trueque_id, receptor_id=receptor_id))
        except TruequeORM.DoesNotExist:
            return None

    def obtener_por_participante(self, trueque_id: int, usuario_id: int) -> Optional[AcuerdoTruequeDominio]:
        from django.db.models import Q
        from backend.comunidad.models import AcuerdoTrueque as TruequeORM
        try:
            return self._modelo_a_dominio(TruequeORM.objects.get(
                Q(id=trueque_id) & (Q(emisor_id=usuario_id) | Q(receptor_id=usuario_id))
            ))
        except TruequeORM.DoesNotExist:
            return None

    @transaction.atomic
    def crear(self, emisor_id: int, receptor_id: int, publicacion_emisor_id: int = None, publicacion_receptor_id: int = None) -> AcuerdoTruequeDominio:
        from backend.comunidad.models import AcuerdoTrueque as TruequeORM
        modelo = TruequeORM.objects.create(
            emisor_id=emisor_id,
            receptor_id=receptor_id,
            publicacion_emisor_id=publicacion_emisor_id,
            publicacion_receptor_id=publicacion_receptor_id,
            estado="PENDIENTE",
        )
        return self._modelo_a_dominio(modelo)

    def obtener_o_crear_pendiente(self, emisor_id: int, receptor_id: int, publicacion_emisor_id: int = None, publicacion_receptor_id: int = None) -> AcuerdoTruequeDominio:
        from django.db.models import Q
        from backend.comunidad.models import AcuerdoTrueque as TruequeORM
        existente = TruequeORM.objects.filter(
            Q(emisor_id=emisor_id, receptor_id=receptor_id) | Q(emisor_id=receptor_id, receptor_id=emisor_id),
            estado="PENDIENTE",
        ).first()
        if existente:
            existente.emisor_id = emisor_id
            existente.receptor_id = receptor_id
            if publicacion_emisor_id is not None:
                existente.publicacion_emisor_id = publicacion_emisor_id
            if publicacion_receptor_id is not None:
                existente.publicacion_receptor_id = publicacion_receptor_id
            existente.save()
            return self._modelo_a_dominio(existente)
        return self.crear(emisor_id, receptor_id, publicacion_emisor_id, publicacion_receptor_id)

    def listar_por_usuario(self, usuario_id: int) -> List[AcuerdoTruequeDominio]:
        from django.db.models import Q
        from backend.comunidad.models import AcuerdoTrueque as TruequeORM
        qs = TruequeORM.objects.filter(
            Q(emisor_id=usuario_id) | Q(receptor_id=usuario_id)
        ).select_related("emisor", "receptor", "publicacion_emisor", "publicacion_receptor")
        return [self._modelo_a_dominio(t) for t in qs]

    @transaction.atomic
    def guardar(self, trueque_dominio: AcuerdoTruequeDominio) -> AcuerdoTruequeDominio:
        from backend.comunidad.models import AcuerdoTrueque as TruequeORM
        modelo = TruequeORM.objects.get(id=trueque_dominio.id)
        modelo.estado = trueque_dominio.estado
        modelo.emisor_confirmado = trueque_dominio.emisor_confirmado
        modelo.receptor_confirmado = trueque_dominio.receptor_confirmado
        modelo.codigo_confirmacion = trueque_dominio.codigo_confirmacion
        modelo.save()
        return trueque_dominio

    # ── Admin Panel (Sprint 2 HU3) ──

    def listar_todos(self, busqueda=None):
        from django.db.models import Q
        from backend.comunidad.models import AcuerdoTrueque as TruequeORM
        qs = TruequeORM.objects.select_related('emisor', 'receptor', 'publicacion_emisor', 'publicacion_receptor').order_by('-id')
        if busqueda:
            qs = qs.filter(
                Q(emisor__username__icontains=busqueda) |
                Q(receptor__username__icontains=busqueda) |
                Q(estado__icontains=busqueda)
            )
        return [self._modelo_a_dominio(t) for t in qs]

    @transaction.atomic
    def actualizar_estado_admin(self, trueque_id, estado):
        from backend.comunidad.models import AcuerdoTrueque as TruequeORM
        modelo = TruequeORM.objects.get(id=trueque_id)
        modelo.estado = estado
        modelo.save()
        return self._modelo_a_dominio(modelo)

    @transaction.atomic
    def eliminar(self, trueque_id):
        from backend.comunidad.models import AcuerdoTrueque as TruequeORM
        TruequeORM.objects.filter(id=trueque_id).delete()


# ── Reseña ────────────────────────────────────────────────────────────────────

class ResenaRepository(IResenaRepository):
    """Implementación del repositorio de Reseñas."""

    def _modelo_a_dominio(self, modelo) -> ResenaDominio:
        return ResenaDominio(
            id=modelo.id,
            trueque_id=modelo.trueque_id,
            calificador_id=modelo.calificador_id,
            calificado_id=modelo.calificado_id,
            estrellas=modelo.estrellas,
            comentario=modelo.comentario,
        )


    @transaction.atomic
    def crear(self, trueque_id: int, calificador_id: int, calificado_id: int, estrellas: int, comentario: str) -> ResenaDominio:
        from backend.comunidad.models import Resena as ResenaORM
        modelo = ResenaORM.objects.create(
            trueque_id=trueque_id,
            calificador_id=calificador_id,
            calificado_id=calificado_id,
            estrellas=estrellas,
            comentario=comentario,
        )
        return self._modelo_a_dominio(modelo)

    def listar_por_calificado(self, usuario_id: int) -> List[ResenaDominio]:
        from backend.comunidad.models import Resena as ResenaORM
        return [
            self._modelo_a_dominio(r)
            for r in ResenaORM.objects.filter(calificado_id=usuario_id)
        ]

    def existe_resena(self, trueque_id: int, calificador_id: int) -> bool:
        from backend.comunidad.models import Resena as ResenaORM
        return ResenaORM.objects.filter(
            trueque_id=trueque_id, calificador_id=calificador_id
        ).exists()

    # ── Admin Panel (Sprint 2 HU3) ──

    def listar_todas(self, busqueda=None):
        from django.db.models import Q
        from backend.comunidad.models import Resena as ResenaORM
        qs = ResenaORM.objects.select_related('calificador', 'calificado', 'trueque').order_by('-id')
        if busqueda:
            qs = qs.filter(
                Q(calificador__username__icontains=busqueda) |
                Q(calificado__username__icontains=busqueda) |
                Q(comentario__icontains=busqueda)
            )
        return [self._modelo_a_dominio(r) for r in qs]

    @transaction.atomic
    def eliminar(self, resena_id):
        from backend.comunidad.models import Resena as ResenaORM
        ResenaORM.objects.filter(id=resena_id).delete()


# ── Notificación ──────────────────────────────────────────────────────────────

class NotificacionRepository(INotificacionRepository):
    """Implementación del repositorio de Notificaciones."""

    def _modelo_a_dominio(self, modelo) -> NotificacionDominio:
        return NotificacionDominio(
            id=modelo.id,
            tipo=modelo.tipo,
            destinatario_id=modelo.destinatario_id,
            remitente_id=modelo.remitente_id,
            trueque_id=modelo.trueque_id,
            trueque_multiple_id=modelo.trueque_multiple_id,
            publicacion_original_id=modelo.publicacion_original_id,
            mensaje=modelo.mensaje,
            estado=modelo.estado,
            match_detalle=modelo.match_detalle,
        )

    def listar_por_destinatario(
        self, usuario_id: int, incluir_leidas: bool = False
    ) -> List[NotificacionDominio]:
        from backend.comunidad.models import NotificacionPropuesta as NotifORM
        qs = NotifORM.objects.filter(destinatario_id=usuario_id)
        if not incluir_leidas:
            qs = qs.exclude(estado='LEIDA')
        return [self._modelo_a_dominio(n) for n in qs.order_by('-prioridad', '-creada_el')]


    def obtener_notificacion_por_id(self, notificacion_id: int) -> Optional[NotificacionDominio]:
        from backend.comunidad.models import NotificacionPropuesta as NotifORM
        try:
            return self._modelo_a_dominio(NotifORM.objects.get(id=notificacion_id))
        except NotifORM.DoesNotExist:
            return None

    @transaction.atomic
    def crear_notificacion(
        self,
        destinatario_id: int,
        remitente_id: int,
        trueque_id: int = None,
        publicacion_original_id: int = None,
        mensaje: str = None,
        tipo: str = "PROPUESTA",
        match_detalle: dict = None,
    ) -> NotificacionDominio:
        from backend.comunidad.models import NotificacionPropuesta as NotifORM
        from backend.comunidad.models import AcuerdoTruequeMultiple
        # Si se recibe un trueque_multiple en match_detalle, utilizar ese campo
        trueque_multiple = None
        if match_detalle and isinstance(match_detalle, dict):
            trueque_multiple = match_detalle.get('trueque_multiple')
            # Si llega un id, intentar resolver la instancia
            try:
                if isinstance(trueque_multiple, int):
                    trueque_multiple = AcuerdoTruequeMultiple.objects.get(id=trueque_multiple)
            except Exception:
                trueque_multiple = None

        modelo = NotifORM.objects.create(
            destinatario_id=destinatario_id,
            remitente_id=remitente_id,
            trueque_id=trueque_id,
            publicacion_original_id=publicacion_original_id,
            mensaje=mensaje,
            match_detalle=match_detalle,
            prioridad=True,
            estado="PENDIENTE",
            tipo=tipo,
            trueque_multiple=trueque_multiple,
        )
        return self._modelo_a_dominio(modelo)

    def existe_match_entre(self, usuario_a_id: int, usuario_b_id: int) -> bool:
        from django.db.models import Q
        from backend.comunidad.models import NotificacionPropuesta as NotifORM
        return NotifORM.objects.filter(
            tipo="MATCH",
            trueque__estado="PENDIENTE",
        ).filter(
            Q(destinatario_id=usuario_a_id, remitente_id=usuario_b_id)
            | Q(destinatario_id=usuario_b_id, remitente_id=usuario_a_id)
        ).exists()


    def actualizar_estado_por_trueque(self, trueque_id: int, nuevo_estado: str) -> int:
        from backend.comunidad.models import NotificacionPropuesta as NotifORM
        return NotifORM.objects.filter(
            trueque_id=trueque_id,
            tipo="PROPUESTA",
        ).update(estado=nuevo_estado)

    def marcar_como_leida(
        self, notificacion_id: int, usuario_id: int
    ) -> NotificacionDominio:
        from django.utils import timezone
        from backend.comunidad.models import NotificacionPropuesta as NotifORM
        notif = NotifORM.objects.get(id=notificacion_id, destinatario_id=usuario_id)
        notif.estado = 'LEIDA'
        notif.leida_el = timezone.now()
        notif.save()
        return self._modelo_a_dominio(notif)

    def marcar_leidas_por_trueque(self, usuario_id: int, trueque_id: int, tipos=None) -> int:
        from backend.comunidad.models import NotificacionPropuesta as NotifORM
        from django.utils import timezone
        tipos = tipos or ("MATCH", "PROPUESTA")
        ahora = timezone.now()
        uid = getattr(usuario_id, 'id', usuario_id)
        tid = getattr(trueque_id, 'id', trueque_id)
        return NotifORM.objects.filter(
            destinatario_id=uid,
            trueque_id=tid,
            tipo__in=tipos,
        ).exclude(estado="LEIDA").update(estado="LEIDA", leida_el=ahora)

    def marcar_leidas_por_trueque_ambos_usuarios(self, trueque_id: int, tipos=None) -> int:
        from backend.comunidad.models import NotificacionPropuesta as NotifORM
        from django.utils import timezone
        tipos = tipos or ("MATCH", "PROPUESTA")
        ahora = timezone.now()
        tid = getattr(trueque_id, 'id', trueque_id)
        return NotifORM.objects.filter(
            trueque_id=tid,
            tipo__in=tipos,
        ).exclude(estado="LEIDA").update(estado="LEIDA", leida_el=ahora)


# ── Trueque Múltiple ──────────────────────────────────────────────────────
class TruequeMultipleRepository:
    """Implementación simplificada para AcuerdoTruequeMultiple."""

    def _modelo_a_dominio(self, modelo):
        from .dominio.entidades import AcuerdoTruequeMultipleDominio
        return AcuerdoTruequeMultipleDominio(
            id=modelo.id,
            estado=modelo.estado,
            emisor1_id=modelo.emisor1_id,
            receptor1_id=modelo.receptor1_id,
            emisor2_id=modelo.emisor2_id,
            receptor2_id=modelo.receptor2_id,
            emisor3_id=modelo.emisor3_id,
            receptor3_id=modelo.receptor3_id,
            usuario1_aceptado=modelo.usuario1_aceptado,
            usuario2_aceptado=modelo.usuario2_aceptado,
            usuario3_aceptado=modelo.usuario3_aceptado,
            par1_confirmado=modelo.par1_confirmado,
            par2_confirmado=modelo.par2_confirmado,
            par3_confirmado=modelo.par3_confirmado,
            fecha_creacion=getattr(modelo, 'fecha_creacion', None),
        )

    def obtener_por_id(self, trueque_multiple_id: int):
        from backend.comunidad.models import AcuerdoTruequeMultiple as TMORM
        try:
            return self._modelo_a_dominio(TMORM.objects.get(id=trueque_multiple_id))
        except TMORM.DoesNotExist:
            return None

    def obtener_bloqueado(self, trueque_id: int):
        from backend.comunidad.models import AcuerdoTruequeMultiple as TMORM
        try:
            return self._modelo_a_dominio(TMORM.objects.select_for_update().get(id=trueque_id))
        except TMORM.DoesNotExist:
            return None

    def obtener_por_participante(self, trueque_id: int, usuario):
        from django.db.models import Q
        from backend.comunidad.models import AcuerdoTruequeMultiple as TMORM
        uid = getattr(usuario, 'id', usuario)
        try:
            return self._modelo_a_dominio(TMORM.objects.get(
                Q(id=trueque_id) & 
                (Q(emisor1_id=uid) | Q(receptor1_id=uid) | 
                 Q(emisor2_id=uid) | Q(receptor2_id=uid) | 
                 Q(emisor3_id=uid) | Q(receptor3_id=uid))
            ))
        except TMORM.DoesNotExist:
            return None

    def usuario_tiene_trueque_multiple_activo(self, usuario):
        from django.db.models import Q
        from backend.comunidad.models import AcuerdoTruequeMultiple as TMORM
        uid = getattr(usuario, 'id', usuario)
        return TMORM.objects.filter(
            Q(emisor1_id=uid) | Q(receptor1_id=uid) | 
            Q(emisor2_id=uid) | Q(receptor2_id=uid) | 
            Q(emisor3_id=uid) | Q(receptor3_id=uid),
            estado__in=['PENDIENTE', 'ACEPTADO', 'EN_CURSO']
        ).exists()

    @transaction.atomic
    def crear(self, datos):
        from backend.comunidad.models import AcuerdoTruequeMultiple as TMORM
        db_datos = {}
        for k, v in datos.items():
            if k in ('emisor1', 'receptor1', 'emisor2', 'receptor2', 'emisor3', 'receptor3', 
                     'publicacion_emisor1', 'publicacion_receptor1', 
                     'publicacion_emisor2', 'publicacion_receptor2', 
                     'publicacion_emisor3', 'publicacion_receptor3'):
                db_datos[f"{k}_id"] = getattr(v, 'id', None)
            else:
                db_datos[k] = v
        modelo = TMORM.objects.create(**db_datos)
        return self._modelo_a_dominio(modelo)

    def guardar(self, trueque_multiple_dominio):
        from backend.comunidad.models import AcuerdoTruequeMultiple as TMORM
        modelo = TMORM.objects.get(id=trueque_multiple_dominio.id)
        modelo.estado = trueque_multiple_dominio.estado
        modelo.usuario1_aceptado = trueque_multiple_dominio.usuario1_aceptado
        modelo.usuario2_aceptado = trueque_multiple_dominio.usuario2_aceptado
        modelo.usuario3_aceptado = trueque_multiple_dominio.usuario3_aceptado
        modelo.par1_confirmado = trueque_multiple_dominio.par1_confirmado
        modelo.par2_confirmado = trueque_multiple_dominio.par2_confirmado
        modelo.par3_confirmado = trueque_multiple_dominio.par3_confirmado
        modelo.save()
        return trueque_multiple_dominio

    def listar_por_usuario(self, usuario_id: int):
        from django.db.models import Q
        from backend.comunidad.models import AcuerdoTruequeMultiple as TMORM
        uid = getattr(usuario_id, 'id', usuario_id)
        qs = TMORM.objects.filter(
            Q(emisor1_id=uid) | Q(receptor1_id=uid) |
            Q(emisor2_id=uid) | Q(receptor2_id=uid) |
            Q(emisor3_id=uid) | Q(receptor3_id=uid)
        )
        return [self._modelo_a_dominio(t) for t in qs]

    # ── Admin Panel (Sprint 2 HU3) ──

    def listar_todos(self, busqueda=None):
        from django.db.models import Q
        from backend.comunidad.models import AcuerdoTruequeMultiple as TMORM
        qs = TMORM.objects.all().order_by('-id')
        if busqueda:
            qs = qs.filter(
                Q(emisor1__username__icontains=busqueda) |
                Q(receptor1__username__icontains=busqueda) |
                Q(estado__icontains=busqueda)
            )
        return [self._modelo_a_dominio(t) for t in qs]

    @transaction.atomic
    def actualizar_estado_admin(self, trueque_multiple_id, estado):
        from backend.comunidad.models import AcuerdoTruequeMultiple as TMORM
        modelo = TMORM.objects.get(id=trueque_multiple_id)
        modelo.estado = estado
        modelo.save()
        return self._modelo_a_dominio(modelo)

    @transaction.atomic
    def eliminar(self, trueque_multiple_id):
        from backend.comunidad.models import AcuerdoTruequeMultiple as TMORM
        TMORM.objects.filter(id=trueque_multiple_id).delete()


# ── Saldo Comercial ───────────────────────────────────────────────────────
class SaldoComercialRepository:
    """Registro simple de movimientos y consulta de saldo."""


    def crear_movimiento(self, comercio_id: int, cliente_id: int, monto: float, tipo_movimiento: str, valor_producto: float = None, monto_recibido: float = None):
        from datetime import timedelta
        from django.utils import timezone
        from backend.comunidad.models import SaldoComercial as SaldoORM

        VIGENCIA_SALDO_COMERCIAL_ANIOS = 12
        fecha_expiracion = timezone.now() + timedelta(days=365 * VIGENCIA_SALDO_COMERCIAL_ANIOS)
        
        return SaldoORM.objects.create(
            comercio_id=comercio_id,
            cliente_id=cliente_id,
            monto_excedente=monto,
            tipo_movimiento=tipo_movimiento,
            fecha_expiracion=fecha_expiracion,
            valor_producto=valor_producto,
            monto_recibido=monto_recibido,
        )

    def listar_por_cliente(self, cliente_id: int):
        from backend.comunidad.models import SaldoComercial as SaldoORM
        return list(SaldoORM.objects.filter(cliente_id=cliente_id).order_by("-fecha"))

    def listar_por_comercio(self, comercio_id: int):
        from backend.comunidad.models import SaldoComercial as SaldoORM
        return list(SaldoORM.objects.filter(comercio_id=comercio_id).order_by("-fecha"))

    def obtener_saldo(self, usuario_id: int) -> float:
        from django.db.models import Sum
        from backend.comunidad.models import SaldoComercial as SaldoORM
        suma = SaldoORM.objects.filter(cliente_id=usuario_id).aggregate(total=Sum('monto_excedente'))
        return float(suma.get('total') or 0.0)

    # ── Admin Panel (Sprint 2 HU3) ──

    def listar_todos(self, busqueda=None):
        from django.db.models import Q
        from backend.comunidad.models import SaldoComercial as SaldoORM
        qs = SaldoORM.objects.select_related('comercio', 'cliente').order_by('-fecha')
        if busqueda:
            qs = qs.filter(
                Q(comercio__username__icontains=busqueda) |
                Q(cliente__username__icontains=busqueda)
            )
        return list(qs.values(
            'id', 'comercio__username', 'cliente__username',
            'monto_excedente', 'tipo_movimiento', 'fecha',
            'valor_producto', 'monto_recibido',
        ))


# ── Usuario Autorizado ────────────────────────────────────────────────────────
class UsuarioAutorizadoRepository:
    def _modelo_a_dominio(self, modelo) -> UsuarioAutorizadoDominio:
        return UsuarioAutorizadoDominio(
            id=modelo.id,
            email=modelo.email,
            tipo=modelo.tipo,
        )

    def existe_email(self, email: str, tipo: str = None) -> bool:
        from backend.comunidad.models import UsuarioAutorizado as ORM
        queryset = ORM.objects.filter(email=email)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        return queryset.exists()

    def guardar_email(self, email: str, tipo: str = "USUARIO") -> tuple[UsuarioAutorizadoDominio, bool]:
        from backend.comunidad.models import UsuarioAutorizado as ORM
        modelo, creado = ORM.objects.update_or_create(
            email=email,
            defaults={"tipo": tipo},
        )
        return self._modelo_a_dominio(modelo), creado


# ── Reseña Múltiple ───────────────────────────────────────────────────────────
class ResenaMultipleRepository:
    def _modelo_a_dominio(self, modelo) -> ResenaMultipleDominio:
        return ResenaMultipleDominio(
            id=modelo.id,
            trueque_multiple_id=modelo.trueque_multiple_id,
            calificador_id=modelo.calificador_id,
            calificado_id=modelo.calificado_id,
            estrellas=modelo.estrellas,
            comentario=modelo.comentario,
        )

    def crear(self, trueque_multiple_id: int, calificador_id: int, calificado_id: int, estrellas: int, comentario: str) -> ResenaMultipleDominio:
        from backend.comunidad.models import ResenaMultiple as ORM
        # Aceptar objeto o id
        tmid = getattr(trueque_multiple_id, 'id', trueque_multiple_id)
        calif_id = getattr(calificador_id, 'id', calificador_id)
        califd_id = getattr(calificado_id, 'id', calificado_id)
        modelo = ORM.objects.create(
            trueque_multiple_id=tmid,
            calificador_id=calif_id,
            calificado_id=califd_id,
            estrellas=estrellas,
            comentario=comentario,
        )
        return self._modelo_a_dominio(modelo)

    def listar_por_calificado(self, usuario_id: int) -> list[ResenaMultipleDominio]:
        from backend.comunidad.models import ResenaMultiple as ORM
        uid = getattr(usuario_id, 'id', usuario_id)
        return [
            self._modelo_a_dominio(r)
            for r in ORM.objects.filter(calificado_id=uid)
        ]

    def existe_resena(self, trueque_multiple_id: int, calificador_id: int, calificado_id: int) -> bool:
        from backend.comunidad.models import ResenaMultiple as ORM
        tmid = getattr(trueque_multiple_id, 'id', trueque_multiple_id)
        calif_id = getattr(calificador_id, 'id', calificador_id)
        califd_id = getattr(calificado_id, 'id', calificado_id)
        return ORM.objects.filter(
            trueque_multiple_id=tmid,
            calificador_id=calif_id,
            calificado_id=califd_id,
        ).exists()

    # ── Admin Panel (Sprint 2 HU3) ──

    def listar_todas(self, busqueda=None):
        from django.db.models import Q
        from backend.comunidad.models import ResenaMultiple as ORM
        qs = ORM.objects.select_related('calificador', 'calificado', 'trueque_multiple').order_by('-id')
        if busqueda:
            qs = qs.filter(
                Q(calificador__username__icontains=busqueda) |
                Q(calificado__username__icontains=busqueda) |
                Q(comentario__icontains=busqueda)
            )
        return [self._modelo_a_dominio(r) for r in qs]

    @transaction.atomic
    def eliminar(self, resena_multiple_id):
        from backend.comunidad.models import ResenaMultiple as ORM
        ORM.objects.filter(id=resena_multiple_id).delete()


# ── Matchmaking ───────────────────────────────────────────────────────────────
class MatchmakingRepository:
    def _modelo_a_dominio(self, modelo) -> UsuarioDominio:
        return UsuarioDominio(
            id=modelo.id,
            username=modelo.username,
            email=modelo.email,
            nombre_real=modelo.nombre_real,
            horas_de_vida=float(modelo.horas_de_vida),
            es_comercio=modelo.es_comercio,
            saldo_comercial=float(modelo.saldo_comercial),
            is_active=modelo.is_active,
            is_staff=modelo.is_staff,
            is_superuser=modelo.is_superuser,
        )

    def _publicacion_a_dominio(self, modelo) -> PublicacionDominio:
        usuario = getattr(modelo, 'usuario', None)
        return PublicacionDominio(
            id=modelo.id,
            usuario_id=modelo.usuario_id,
            tipo=modelo.tipo,
            titulo=modelo.titulo,
            descripcion=modelo.descripcion,
            categoria=modelo.categoria,
            urgencia=modelo.urgencia,
            esta_activa=modelo.esta_activa,
            usuario_nombre_real=getattr(usuario, 'nombre_real', '') or '',
            usuario_promedio_estrellas=float(getattr(usuario, 'promedio_estrellas', 0.0) or 0.0),
            usuario_username=getattr(usuario, 'username', '') or '',
            usuario_is_active=getattr(usuario, 'is_active', True),
            usuario_horas_de_vida=float(getattr(usuario, 'horas_de_vida', 0.0) or 0.0),
        )

    def _construir_match_enriquecido(self, usuario_id: int, candidato_orm, titulos_necesidades: list[str], titulos_talentos: list[str]) -> dict:
        from backend.comunidad.models import Publicacion as PublicacionORM
        uid = getattr(usuario_id, 'id', usuario_id)
        mis_talentos = [
            self._publicacion_a_dominio(p)
            for p in PublicacionORM.objects.select_related('usuario').filter(
                usuario_id=uid,
                tipo="TALENTO",
                esta_activa=True,
                titulo__in=titulos_talentos,
            )
        ]
        mis_necesidades = [
            self._publicacion_a_dominio(p)
            for p in PublicacionORM.objects.select_related('usuario').filter(
                usuario_id=uid,
                tipo="NECESIDAD",
                esta_activa=True,
                titulo__in=titulos_necesidades,
            )
        ]
        talentos_coincidentes = [
            self._publicacion_a_dominio(p)
            for p in PublicacionORM.objects.select_related('usuario').filter(
                usuario_id=candidato_orm.id,
                tipo="TALENTO",
                esta_activa=True,
                titulo__in=titulos_necesidades,
            )
        ]
        necesidades_coincidentes = [
            self._publicacion_a_dominio(p)
            for p in PublicacionORM.objects.select_related('usuario').filter(
                usuario_id=candidato_orm.id,
                tipo="NECESIDAD",
                esta_activa=True,
                titulo__in=titulos_talentos,
            )
        ]

        publicaciones_sugeridas = []
        for mi_nec in mis_necesidades:
            for su_tal in talentos_coincidentes:
                if mi_nec.titulo == su_tal.titulo:
                    publicaciones_sugeridas.append(
                        {"mi_pub_id": mi_nec.id, "su_pub_id": su_tal.id}
                    )
        for mi_tal in mis_talentos:
            for su_nec in necesidades_coincidentes:
                if mi_tal.titulo == su_nec.titulo:
                    publicaciones_sugeridas.append(
                        {"mi_pub_id": mi_tal.id, "su_pub_id": su_nec.id}
                    )

        return {
            "usuario": self._modelo_a_dominio(candidato_orm),
            "talentos_coincidentes": talentos_coincidentes,
            "necesidades_coincidentes": necesidades_coincidentes,
            "publicaciones_sugeridas": publicaciones_sugeridas,
        }

    def buscar_matches(self, usuario_id: int, titulos_necesidades: list[str], titulos_talentos: list[str]) -> list:
        if not titulos_necesidades or not titulos_talentos:
            return []

        from backend.comunidad.models import Usuario as UsuarioORM
        uid = getattr(usuario_id, 'id', usuario_id)
        candidatos = (
            UsuarioORM.objects.filter(
                publicaciones__tipo="TALENTO",
                publicaciones__titulo__in=titulos_necesidades,
                publicaciones__esta_activa=True,
            )
            .filter(
                publicaciones__tipo="NECESIDAD",
                publicaciones__titulo__in=titulos_talentos,
                publicaciones__esta_activa=True,
            )
            .exclude(id=uid)
            .distinct()
        )

        return [
            self._construir_match_enriquecido(
                uid, candidato, titulos_necesidades, titulos_talentos
            )
            for candidato in candidatos
        ]

    def verificar_coincidencia_por_titulo(self, usuario_id: int, publicacion_seleccionada: PublicacionDominio) -> dict:
        if not publicacion_seleccionada or not publicacion_seleccionada.titulo:
            return {
                "tiene_coincidencia": False,
                "publicaciones_coincidentes": [],
                "tipo_buscado": None,
                "titulo": None
            }
        
        tipo_buscado = "NECESIDAD" if publicacion_seleccionada.tipo == "TALENTO" else "TALENTO"
        uid = getattr(usuario_id, 'id', usuario_id)
        
        from backend.comunidad.models import Publicacion as PublicacionORM
        publicaciones_coincidentes = [
            self._publicacion_a_dominio(p)
            for p in PublicacionORM.objects.filter(
                usuario_id=uid,
                titulo=publicacion_seleccionada.titulo,
                tipo=tipo_buscado,
                esta_activa=True,
            )
        ]
        
        return {
            "tiene_coincidencia": len(publicaciones_coincidentes) > 0,
            "publicaciones_coincidentes": publicaciones_coincidentes,
            "tipo_buscado": tipo_buscado,
            "titulo": publicacion_seleccionada.titulo
        }

    def buscar_matches_por_publicacion(self, usuario_id: int, publicacion: PublicacionDominio) -> list:
        if not publicacion or not publicacion.titulo:
            return []

        tipo_buscado = "NECESIDAD" if publicacion.tipo == "TALENTO" else "TALENTO"
        tipo_propio = "TALENTO" if publicacion.tipo == "NECESIDAD" else "NECESIDAD"
        uid = getattr(usuario_id, 'id', usuario_id)

        from backend.comunidad.models import Usuario as UsuarioORM
        from backend.comunidad.models import Publicacion as PublicacionORM
        candidatos = (
            UsuarioORM.objects.filter(
                publicaciones__tipo=tipo_buscado,
                publicaciones__titulo=publicacion.titulo,
                publicaciones__esta_activa=True,
            )
            .exclude(id=uid)
            .distinct()
        )

        resultados = []
        for candidato in candidatos:
            pubs_complementarias = [
                self._publicacion_a_dominio(p)
                for p in PublicacionORM.objects.filter(
                    usuario_id=candidato.id,
                    tipo=tipo_buscado,
                    titulo=publicacion.titulo,
                    esta_activa=True,
                )
            ]
            mis_complementarias = [
                self._publicacion_a_dominio(p)
                for p in PublicacionORM.objects.filter(
                    usuario_id=uid,
                    tipo=tipo_propio,
                    esta_activa=True,
                )
            ]
            titulos_mis_complementarias = {pub.titulo for pub in mis_complementarias}
            talentos_coincidentes = []
            necesidades_coincidentes = []
            if tipo_buscado == "TALENTO":
                talentos_coincidentes = pubs_complementarias
                necesidades_coincidentes = [
                    self._publicacion_a_dominio(p)
                    for p in PublicacionORM.objects.filter(
                        usuario_id=candidato.id,
                        tipo="NECESIDAD",
                        titulo__in=titulos_mis_complementarias,
                        esta_activa=True,
                    )
                ]
            else:
                necesidades_coincidentes = pubs_complementarias
                talentos_coincidentes = [
                    self._publicacion_a_dominio(p)
                    for p in PublicacionORM.objects.filter(
                        usuario_id=candidato.id,
                        tipo="TALENTO",
                        titulo__in=titulos_mis_complementarias,
                        esta_activa=True,
                    )
                ]

            if not talentos_coincidentes or not necesidades_coincidentes:
                continue

            titulos_necesidades = (
                [publicacion.titulo]
                if publicacion.tipo == "NECESIDAD"
                else [pub.titulo for pub in necesidades_coincidentes]
            )
            titulos_talentos = (
                [publicacion.titulo]
                if publicacion.tipo == "TALENTO"
                else [pub.titulo for pub in talentos_coincidentes]
            )
            resultados.append(
                self._construir_match_enriquecido(
                    uid, candidato, titulos_necesidades, titulos_talentos
                )
            )

        return resultados


# ── Sprint 2 HU1: Impacto Social ─────────────────────────────────────────────

class SolicitudApoyoSocialRepository:
    """
    Persistencia de solicitudes de apoyo social.
    Mapea entre SolicitudApoyoSocial ORM y SolicitudApoyoSocialDominio.
    """

    def _modelo_a_dominio(self, modelo) -> SolicitudApoyoSocialDominio:
        necesidad_activa = False
        if modelo.publicacion_id is not None:
            pub = getattr(modelo, 'publicacion', None)
            if pub is not None:
                necesidad_activa = pub.esta_activa
        return SolicitudApoyoSocialDominio(
            id=modelo.id,
            solicitante_id=modelo.solicitante_id,
            categoria=modelo.categoria,
            titulo=modelo.titulo,
            descripcion=modelo.descripcion,
            estado=modelo.estado,
            horas_recibidas=float(modelo.horas_recibidas),
            horas_solidarias_disponibles=float(modelo.horas_solidarias_disponibles),
            horas_solidarias_utilizadas=float(modelo.horas_solidarias_utilizadas),
            publicacion_id=modelo.publicacion_id,
            aprobada_por_id=modelo.aprobada_por_id,
            creado_el=modelo.creado_el,
            actualizado_el=modelo.actualizado_el,
            solicitante_nombre=getattr(modelo.solicitante, 'nombre_real', ''),
            estado_social_solicitante=getattr(modelo.solicitante, 'estado_social', 'NINGUNO'),
            necesidad_activa=necesidad_activa,
        )

    def crear(self, solicitante_id: int, categoria: str, titulo: str, descripcion: str):
        """Crea una solicitud en estado PENDIENTE y retorna el ORM (para serializar)."""
        from backend.comunidad.models import SolicitudApoyoSocial
        return SolicitudApoyoSocial.objects.create(
            solicitante_id=solicitante_id,
            categoria=categoria,
            titulo=titulo,
            descripcion=descripcion,
            estado="PENDIENTE",
        )

    def obtener_orm(self, solicitud_id: int):
        """Retorna el ORM o None si no existe."""
        from backend.comunidad.models import SolicitudApoyoSocial
        try:
            return SolicitudApoyoSocial.objects.select_related('solicitante', 'publicacion').get(id=solicitud_id)
        except SolicitudApoyoSocial.DoesNotExist:
            return None

    def listar_aprobadas(self) -> list:
        """Lista solicitudes aprobadas como lista de dicts para el endpoint público."""
        from backend.comunidad.models import SolicitudApoyoSocial
        solicitudes = (
            SolicitudApoyoSocial.objects
            .filter(estado="APROBADA")
            .select_related("solicitante")
            .order_by("-id")
        )
        return [
            {
                "id": s.id,
                "categoria": s.categoria,
                "titulo": s.titulo,
                "descripcion": s.descripcion,
                "horas_recibidas": s.horas_recibidas,
                "estado_social_solicitante": s.solicitante.estado_social,
                "solicitante_id": s.solicitante_id,
                "solicitante_nombre": s.solicitante.nombre_real,
                "horas_recibidas_donacion_solicitante": s.solicitante.horas_recibidas_donacion,
                "horas_de_vida_solicitante": s.solicitante.horas_de_vida,
            }
            for s in solicitudes
        ]

    def listar_por_solicitante(self, usuario_id: int):
        """Lista ORM de solicitudes del usuario para serializar directamente."""
        from backend.comunidad.models import SolicitudApoyoSocial
        return list(
            SolicitudApoyoSocial.objects
            .filter(solicitante_id=usuario_id)
            .select_related('publicacion')
            .order_by("-id")
        )

    def listar_pendientes(self):
        """Lista ORM de solicitudes pendientes para el admin."""
        from backend.comunidad.models import SolicitudApoyoSocial
        return list(
            SolicitudApoyoSocial.objects
            .filter(estado="PENDIENTE")
            .select_related("solicitante")
            .order_by("creado_el")
        )

    def vincular_publicacion(self, solicitud_id: int, publicacion_id: int):
        """Vincula una publicación de causa social a la solicitud."""
        from backend.comunidad.models import SolicitudApoyoSocial
        SolicitudApoyoSocial.objects.filter(id=solicitud_id).update(publicacion_id=publicacion_id)

    def aprobar(self, solicitud_id: int, admin_id: int):
        """Aprueba una solicitud y marca al solicitante como VULNERABLE si es NINGUNO.

        Retorna (solicitud_orm, marcado_vulnerable: bool).
        Toda la operación es atómica (caller debe envolver en transaction.atomic si necesario).
        """
        from backend.comunidad.models import SolicitudApoyoSocial, Usuario as UsuarioORM
        sol = SolicitudApoyoSocial.objects.select_for_update().get(id=solicitud_id)
        sol.estado = "APROBADA"
        sol.aprobada_por_id = admin_id
        sol.save(update_fields=["estado", "aprobada_por"])

        solicitante = UsuarioORM.objects.select_for_update().get(id=sol.solicitante_id)
        marcado_vulnerable = False
        if solicitante.estado_social == "NINGUNO":
            solicitante.estado_social = "VULNERABLE"
            solicitante.save(update_fields=["estado_social"])
            marcado_vulnerable = True

        sol.refresh_from_db()
        sol.solicitante.refresh_from_db()
        return sol, marcado_vulnerable

    def rechazar(self, solicitud_id: int, admin_id: int):
        """Rechaza una solicitud pendiente. Retorna el ORM actualizado."""
        from backend.comunidad.models import SolicitudApoyoSocial
        sol = SolicitudApoyoSocial.objects.get(id=solicitud_id)
        sol.estado = "RECHAZADA"
        sol.aprobada_por_id = admin_id
        sol.save(update_fields=["estado", "aprobada_por"])
        return sol

    def obtener_solicitudes_aprobadas_de_usuario(self, usuario_id: int) -> list:
        """Retorna lista de solicitudes aprobadas de un usuario específico."""
        from backend.comunidad.models import SolicitudApoyoSocial
        return list(
            SolicitudApoyoSocial.objects.filter(
                solicitante_id=usuario_id, estado="APROBADA"
            ).select_related("solicitante")
        )

    def resolver_solicitud_asignacion(self, receptor_id: int, solicitud_id=None):
        """Resuelve la solicitud destino para asignación desde fondo.

        Si se da un solicitud_id, lo verifica; si no, busca la única aprobada.
        Retorna el ORM de la solicitud.
        """
        from backend.comunidad.models import SolicitudApoyoSocial
        from backend.comunidad.services.base import BusinessError

        if solicitud_id is not None:
            try:
                solicitud = SolicitudApoyoSocial.objects.get(id=solicitud_id)
            except SolicitudApoyoSocial.DoesNotExist:
                raise BusinessError("Solicitud no encontrada.", status_code=404)
        else:
            solicitudes = SolicitudApoyoSocial.objects.filter(
                solicitante_id=receptor_id, estado="APROBADA"
            )
            cantidad = solicitudes.count()
            if cantidad == 0:
                raise BusinessError("El usuario no tiene solicitudes aprobadas.")
            if cantidad > 1:
                raise BusinessError("Debes indicar la solicitud a la que asignar las horas.")
            solicitud = solicitudes.first()

        if solicitud.estado != "APROBADA":
            raise BusinessError("Solo se puede asignar a solicitudes aprobadas.")
        if solicitud.solicitante_id != receptor_id:
            raise BusinessError("La solicitud no pertenece al usuario receptor.")
        return solicitud


class DonacionHorasRepository:
    """
    Persistencia del ledger inmutable de donaciones de Horas de Vida.
    """

    def crear_orm(self, donante_id: int, receptor_id: int, solicitud_id, monto: float, tipo_destino: str):
        """Crea una donación y retorna el ORM para serializar."""
        from backend.comunidad.models import DonacionHoras
        return DonacionHoras.objects.create(
            donante_id=donante_id,
            receptor_id=receptor_id,
            solicitud_id=solicitud_id,
            monto=monto,
            tipo_destino=tipo_destino,
        )

    def listar_por_donante(self, usuario_id: int):
        """Retorna queryset de donaciones realizadas."""
        from backend.comunidad.models import DonacionHoras
        return (
            DonacionHoras.objects
            .filter(donante_id=usuario_id)
            .select_related("donante", "receptor", "solicitud")
            .order_by("-fecha")
        )

    def listar_por_receptor(self, usuario_id: int):
        """Retorna queryset de donaciones recibidas."""
        from backend.comunidad.models import DonacionHoras
        return (
            DonacionHoras.objects
            .filter(receptor_id=usuario_id)
            .select_related("donante", "receptor", "solicitud")
            .order_by("-fecha")
        )

    def ejecutar_donacion_a_causa(self, donante_id: int, receptor_id: int, solicitud_id: int, monto: float) -> dict:
        """Transfiere horas del donante al receptor de una causa (atómico).

        Retorna dict con datos del resultado.
        """
        from backend.comunidad.models import Usuario as UsuarioORM, SolicitudApoyoSocial, DonacionHoras
        donante = UsuarioORM.objects.select_for_update().get(id=donante_id)
        receptor = UsuarioORM.objects.select_for_update().get(id=receptor_id)
        solicitud = SolicitudApoyoSocial.objects.select_for_update().get(id=solicitud_id)

        donante.horas_de_vida -= monto
        receptor.horas_recibidas_donacion += monto
        receptor.horas_de_vida += monto
        solicitud.horas_solidarias_disponibles += monto
        solicitud.horas_recibidas += monto

        donante.save(update_fields=["horas_de_vida"])
        receptor.save(update_fields=["horas_de_vida", "horas_recibidas_donacion"])
        solicitud.save(update_fields=["horas_solidarias_disponibles", "horas_recibidas"])

        donacion = DonacionHoras.objects.create(
            donante_id=donante.id, receptor_id=receptor.id,
            solicitud_id=solicitud_id, monto=monto, tipo_destino="CAUSA",
        )
        return {
            "donante_saldo": donante.horas_de_vida,
            "receptor_nombre": receptor.nombre_real,
            "receptor_id": receptor.id,
            "donacion_id": donacion.id,
            "comprobante_id": str(donacion.comprobante_id),
        }

    def ejecutar_donacion_a_fondo(self, donante_id: int, fondo_id: int, monto: float) -> dict:
        """Transfiere horas del donante al fondo comunitario (atómico).

        Retorna dict con datos del resultado.
        """
        from backend.comunidad.models import Usuario as UsuarioORM, DonacionHoras
        donante = UsuarioORM.objects.select_for_update().get(id=donante_id)
        fondo = UsuarioORM.objects.select_for_update().get(id=fondo_id)

        donante.horas_de_vida -= monto
        fondo.horas_de_vida += monto

        donante.save(update_fields=["horas_de_vida"])
        fondo.save(update_fields=["horas_de_vida"])

        donacion = DonacionHoras.objects.create(
            donante_id=donante.id, receptor_id=fondo.id,
            solicitud_id=None, monto=monto, tipo_destino="FONDO",
        )
        return {
            "donante_saldo": donante.horas_de_vida,
            "receptor_nombre": fondo.nombre_real,
            "receptor_id": fondo.id,
            "donacion_id": donacion.id,
            "comprobante_id": str(donacion.comprobante_id),
        }

    def ejecutar_asignacion_fondo(self, fondo_id: int, receptor_id: int, solicitud_id: int, monto: float) -> dict:
        """Transfiere horas del fondo comunitario a un receptor vulnerable (atómico).

        Retorna dict con datos del resultado.
        """
        from backend.comunidad.models import Usuario as UsuarioORM, SolicitudApoyoSocial, DonacionHoras
        from backend.comunidad.services.base import BusinessError

        fondo = UsuarioORM.objects.select_for_update().get(id=fondo_id)
        receptor = UsuarioORM.objects.select_for_update().get(id=receptor_id)
        solicitud = SolicitudApoyoSocial.objects.select_for_update().get(id=solicitud_id)

        if fondo.horas_de_vida < monto:
            raise BusinessError("El fondo comunitario no tiene saldo suficiente.")

        fondo.horas_de_vida -= monto
        receptor.horas_recibidas_donacion += monto
        receptor.horas_de_vida += monto
        solicitud.horas_solidarias_disponibles += monto
        solicitud.horas_recibidas += monto

        fondo.save(update_fields=["horas_de_vida"])
        receptor.save(update_fields=["horas_de_vida", "horas_recibidas_donacion"])
        solicitud.save(update_fields=["horas_solidarias_disponibles", "horas_recibidas"])

        donacion = DonacionHoras.objects.create(
            donante_id=fondo.id, receptor_id=receptor.id,
            solicitud_id=solicitud.id, monto=monto, tipo_destino="ASIGNACION",
        )
        return {
            "saldo_fondo": fondo.horas_de_vida,
            "receptor_id": receptor.id,
            "receptor_saldo": receptor.horas_de_vida,
            "solicitud_id": solicitud.id,
            "horas_solidarias_disponibles": solicitud.horas_solidarias_disponibles,
            "donacion_id": donacion.id,
            "comprobante_id": str(donacion.comprobante_id),
        }


class UsuarioSocialRepository:
    """Repositorio auxiliar para operaciones de estado social de usuarios.

    Centraliza accesos ORM de gestión social que estaban en el servicio.
    """

    def obtener_fondo_comunitario(self):
        """Retorna el usuario ORM del fondo comunitario."""
        from backend.comunidad.models import Usuario as UsuarioORM
        from backend.comunidad.services.base import BusinessError
        try:
            return UsuarioORM.objects.get(username="fondo_comunitario", es_fondo_comunitario=True)
        except UsuarioORM.DoesNotExist:
            raise BusinessError("Fondo comunitario no configurado.", status_code=500)

    def listar_usuarios_regulares(self) -> list:
        """Lista usuarios regulares para gestión de estado social por admin."""
        from backend.comunidad.models import Usuario as UsuarioORM
        return list(
            UsuarioORM.objects.filter(
                is_active=True,
                es_comercio=False,
                is_staff=False,
                is_superuser=False,
                es_fondo_comunitario=False,
            ).order_by("nombre_real", "username")
        )

    def actualizar_estado_social(self, usuario_id: int, estado_social: str):
        """Actualiza el estado social de un usuario. Retorna el ORM actualizado."""
        from backend.comunidad.models import Usuario as UsuarioORM
        from backend.comunidad.services.base import BusinessError
        try:
            usuario = UsuarioORM.objects.get(id=usuario_id)
        except UsuarioORM.DoesNotExist:
            raise BusinessError("Usuario no encontrado.", status_code=404)

        if usuario.es_fondo_comunitario or usuario.es_comercio:
            raise BusinessError("No se puede modificar el estado social de este usuario.")

        usuario.estado_social = estado_social
        usuario.save(update_fields=["estado_social"])
        return usuario

    def obtener_receptor_para_donacion(self, solicitud_id: int):
        """Obtiene la solicitud ORM con su solicitante para validar donación.

        Retorna el ORM de la solicitud con select_related('solicitante').
        """
        from backend.comunidad.models import SolicitudApoyoSocial
        from backend.comunidad.services.base import BusinessError
        try:
            return SolicitudApoyoSocial.objects.select_related("solicitante").get(id=solicitud_id)
        except SolicitudApoyoSocial.DoesNotExist:
            raise BusinessError("Solicitud no encontrada.", status_code=404)

    def obtener_receptor_orm(self, usuario_id: int):
        """Obtiene un usuario ORM por ID."""
        from backend.comunidad.models import Usuario as UsuarioORM
        from backend.comunidad.services.base import BusinessError
        try:
            return UsuarioORM.objects.get(id=usuario_id)
        except UsuarioORM.DoesNotExist:
            raise BusinessError("Usuario no encontrado.", status_code=404)


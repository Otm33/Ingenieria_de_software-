from typing import List, Optional

from django.db import transaction
from django.contrib.auth.hashers import make_password

from .dominio.entidades import (
    AcuerdoTruequeDominio,
    NotificacionDominio,
    PublicacionDominio,
    ResenaDominio,
    UsuarioDominio,
)
from .repositorios_interfaces import (
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
        )

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
        from backend.comunidad.models import Usuario as UsuarioORM
        return [
            self._modelo_a_dominio(u)
            for u in UsuarioORM.objects.filter(
                is_active=True, is_staff=False, is_superuser=False
            ).order_by("nombre_real", "username")
        ]

    def listar_comercios_activos(self) -> List[UsuarioDominio]:
        from backend.comunidad.models import Usuario as UsuarioORM
        return [
            self._modelo_a_dominio(u)
            for u in UsuarioORM.objects.filter(es_comercio=True, is_active=True)
        ]

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
            )
            if password:
                modelo.password = make_password(password)
            modelo.save()
            usuario_dominio.id = modelo.id
        return usuario_dominio


# ── Publicación ───────────────────────────────────────────────────────────────

class PublicacionRepository(IPublicacionRepository):
    """
    Implementación del repositorio de Publicaciones usando Django ORM.
    """

    def _modelo_a_dominio(self, modelo) -> PublicacionDominio:
        return PublicacionDominio(
            id=modelo.id,
            usuario_id=modelo.usuario_id,
            tipo=modelo.tipo,
            titulo=modelo.titulo,
            descripcion=modelo.descripcion,
            categoria=modelo.categoria,
            urgencia=modelo.urgencia,
            esta_activa=modelo.esta_activa,
        )

    def obtener_por_id(self, publicacion_id: int) -> Optional[PublicacionDominio]:
        from backend.comunidad.models import Publicacion as PublicacionORM
        try:
            return self._modelo_a_dominio(PublicacionORM.objects.get(id=publicacion_id))
        except PublicacionORM.DoesNotExist:
            return None

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
        from django.db.models import Case, IntegerField, Value, When
        from backend.comunidad.models import Publicacion as PublicacionORM

        qs = PublicacionORM.objects.filter(esta_activa=True)
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
        return [self._modelo_a_dominio(p) for p in qs]

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
        modelo.save()
        return trueque_dominio


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

    def guardar(self, resena_dominio: ResenaDominio) -> ResenaDominio:
        from backend.comunidad.models import Resena as ResenaORM
        modelo = ResenaORM.objects.create(
            trueque_id=resena_dominio.trueque_id,
            calificador_id=resena_dominio.calificador_id,
            calificado_id=resena_dominio.calificado_id,
            estrellas=resena_dominio.estrellas,
            comentario=resena_dominio.comentario,
        )
        resena_dominio.id = modelo.id
        return resena_dominio

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
        )

    def listar_por_destinatario(
        self, usuario_id: int, incluir_leidas: bool = False
    ) -> List[NotificacionDominio]:
        from backend.comunidad.models import NotificacionPropuesta as NotifORM
        qs = NotifORM.objects.filter(destinatario_id=usuario_id)
        if not incluir_leidas:
            qs = qs.exclude(estado='LEIDA')
        return [self._modelo_a_dominio(n) for n in qs.order_by('-prioridad', '-creada_el')]

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
        )

    def obtener_por_id(self, trueque_multiple_id: int):
        from backend.comunidad.models import AcuerdoTruequeMultiple as TMORM
        try:
            return self._modelo_a_dominio(TMORM.objects.get(id=trueque_multiple_id))
        except TMORM.DoesNotExist:
            return None

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
        qs = TMORM.objects.filter(
            Q(emisor1_id=usuario_id) | Q(receptor1_id=usuario_id) |
            Q(emisor2_id=usuario_id) | Q(receptor2_id=usuario_id) |
            Q(emisor3_id=usuario_id) | Q(receptor3_id=usuario_id)
        )
        return [self._modelo_a_dominio(t) for t in qs]


# ── Saldo Comercial ───────────────────────────────────────────────────────
class SaldoComercialRepository:
    """Registro simple de movimientos y consulta de saldo."""

    def registrar_movimiento(self, comercio_id: int, cliente_id: int, monto: float, tipo: str):
        from backend.comunidad.models import SaldoComercial as SaldoORM
        SaldoORM.objects.create(
            comercio_id=comercio_id,
            cliente_id=cliente_id,
            monto_excedente=monto,
            tipo_movimiento=tipo,
        )

    def obtener_saldo(self, usuario_id: int) -> float:
        from django.db.models import Sum
        from backend.comunidad.models import SaldoComercial as SaldoORM
        suma = SaldoORM.objects.filter(cliente_id=usuario_id).aggregate(total=Sum('monto_excedente'))
        return float(suma.get('total') or 0.0)

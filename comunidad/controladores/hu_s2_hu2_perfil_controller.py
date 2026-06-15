"""
Sprint 2 HU 2: Como usuario, quiero ver el historial detallado de todos mis trueques pasados,
mi saldo disponible, mi balance final de deudas y créditos para gestionar mi participación.
"""


class PerfilHistorialController:
    """Controlador para Sprint 2 HU 2 — Perfil e historial de trueques."""

    def __init__(self, usuario_repository, publicacion_repository, resena_repository, trueque_repository):
        self._usu_repo = usuario_repository
        self._pub_repo = publicacion_repository
        self._resena_repo = resena_repository
        self._trueque_repo = trueque_repository

    def ver_mi_perfil(self, usuario_orm) -> dict:
        from comunidad.models import AcuerdoTrueque, Publicacion, Resena
        from comunidad.serializers import PublicacionSerializer, ResenaSerializer, UsuarioSerializer

        publicaciones = Publicacion.objects.filter(usuario=usuario_orm)
        publicaciones_activas = [p for p in publicaciones if p.esta_activa]
        publicaciones_pausadas = [p for p in publicaciones if not p.esta_activa]
        resenas_recibidas = Resena.objects.filter(calificado=usuario_orm)
        resenas_data = ResenaSerializer(resenas_recibidas, many=True).data
        trueques_enviados = AcuerdoTrueque.objects.filter(emisor=usuario_orm)
        trueques_recibidos = AcuerdoTrueque.objects.filter(receptor=usuario_orm)

        nombre = (usuario_orm.nombre_real or "").strip()
        tiene_publicaciones = len(publicaciones) > 0
        es_miembro = bool(nombre and tiene_publicaciones)

        return {
            "usuario": UsuarioSerializer(usuario_orm).data,
            "promedio_estrellas": usuario_orm.promedio_estrellas,
            "publicaciones": PublicacionSerializer(publicaciones, many=True).data,
            "publicaciones_activas": PublicacionSerializer(publicaciones_activas, many=True).data,
            "publicaciones_pausadas": PublicacionSerializer(publicaciones_pausadas, many=True).data,
            "resenas_recibidas": resenas_data,
            "cantidad_resenas": len(resenas_data),
            "trueques_enviados_count": trueques_enviados.count(),
            "trueques_recibidos_count": trueques_recibidos.count(),
            "saldo_comercial": float(usuario_orm.saldo_comercial),
            "es_miembro_activo": es_miembro,
            "cantidad_publicaciones_pausadas": len(publicaciones_pausadas),
        }

    def ver_perfil_otro(self, usuario_id: int) -> dict:
        from comunidad.models import Publicacion, Resena, Usuario as UsuarioORM
        from comunidad.repositorios_implementacion import UsuarioRepository
        from comunidad.serializers import PublicacionSerializer, ResenaSerializer, UsuarioSerializer

        usuario_repo = UsuarioRepository()
        usuario = usuario_repo.obtener_por_id(usuario_id)
        if not usuario:
            raise ValueError("Usuario no encontrado.")

        usuario_orm = UsuarioORM.objects.get(id=usuario.id)
        publicaciones_activas = Publicacion.objects.filter(usuario=usuario_orm, esta_activa=True)
        resenas_recibidas = Resena.objects.filter(calificado=usuario_orm)
        pub_data = PublicacionSerializer(publicaciones_activas, many=True).data
        resenas_data = ResenaSerializer(resenas_recibidas, many=True).data

        return {
            "usuario": UsuarioSerializer(usuario_orm).data,
            "nombre_real": usuario_orm.nombre_real,
            "promedio_estrellas": usuario_orm.promedio_estrellas,
            "publicaciones": pub_data,
            "resenas": resenas_data,
            "cantidad_publicaciones": len(pub_data),
            "cantidad_resenas": len(resenas_data),
        }

    def listar_comunidad(self) -> dict:
        from comunidad.models import Publicacion, Usuario

        miembros = Usuario.objects.filter(
            is_active=True, is_staff=False, is_superuser=False
        ).order_by("nombre_real", "username")

        directorio = []
        for miembro in miembros:
            publicaciones = Publicacion.objects.filter(usuario=miembro)
            talentos_activos = [
                p for p in publicaciones
                if p.tipo == "TALENTO" and p.esta_activa
            ]
            nombre = (miembro.nombre_real or "").strip()
            es_miembro = bool(nombre and len(publicaciones) > 0)

            directorio.append({
                "id": miembro.id,
                "nombre_real": miembro.nombre_real,
                "username": miembro.username,
                "promedio_estrellas": miembro.promedio_estrellas,
                "talentos_principales": [p.titulo for p in talentos_activos[:3]],
                "cantidad_talentos": len(talentos_activos),
                "es_miembro_activo": es_miembro,
            })

        return {
            "miembros": directorio,
            "cantidad": len(directorio),
        }

    def listar_mis_trueques(self, usuario_orm, request=None) -> dict:
        from comunidad.serializers import AcuerdoTruequeSerializer

        trueques = self._trueque_repo.listar_por_usuario(usuario_orm)
        serializer = AcuerdoTruequeSerializer(trueques, many=True, context={"request": request})
        return {
            "trueques": serializer.data,
            "cantidad": len(serializer.data),
        }

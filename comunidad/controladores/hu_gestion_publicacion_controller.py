from comunidad.dto.request_models import ActualizarPublicacionRequest


class GestionPublicacionController:
    """
    Controlador para la Historia de Usuario: Gestión de Publicaciones.
    Cubre: actualizar estado (activar/pausar), listar mis publicaciones, cartelera.
    """

    def __init__(self, publicacion_service, publicacion_repository):
        self._pub_service = publicacion_service
        self._pub_repo = publicacion_repository

    def actualizar_estado(
        self,
        usuario_orm,
        publicacion_id: int,
        request: ActualizarPublicacionRequest,
    ) -> dict:
        """
        Activa o pausa una publicación del usuario.
        Valida que esta_activa sea booleano antes de llamar al service.
        """
        if not isinstance(request.esta_activa, bool):
            raise ValueError("El campo 'esta_activa' es obligatorio y debe ser booleano.")

        from comunidad.serializers import PublicacionSerializer
        publicacion = self._pub_service.actualizar_estado_publicacion(
            usuario_orm, publicacion_id, request.esta_activa
        )
        return PublicacionSerializer(publicacion).data

    def listar_mis_publicaciones(self, usuario_orm) -> dict:
        """Retorna todas las publicaciones del usuario autenticado."""
        from comunidad.models import Publicacion
        from comunidad.serializers import PublicacionSerializer

        # Usar ORM directamente para serialización (serializer necesita objetos ORM)
        publicaciones = Publicacion.objects.filter(usuario=usuario_orm)
        data = PublicacionSerializer(publicaciones, many=True).data
        return {
            "publicaciones": data,
            "cantidad": len(data),
        }

    def obtener_cartelera(self, categoria=None, urgencias=None) -> list:
        """Retorna publicaciones activas ordenadas por urgencia."""
        from django.db.models import Case, IntegerField, Value, When
        from comunidad.models import Publicacion
        from comunidad.serializers import PublicacionSerializer

        # Usar ORM directamente para serialización (serializer necesita objetos ORM)
        qs = Publicacion.objects.filter(esta_activa=True)
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

        return PublicacionSerializer(qs, many=True).data

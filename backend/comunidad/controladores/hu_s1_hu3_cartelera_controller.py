"""
Sprint 1 HU 3: Como usuario, quiero visualizar una cartelera principal
y usar filtros (por categoría, emergencias de urgencia alta o necesidades críticas).
"""


class CarteleraController:
    """Controlador para Sprint 1 HU 3 — Cartelera con filtros."""

    def __init__(self, publicacion_repository):
        self._pub_repo = publicacion_repository

    def obtener_cartelera(self, categoria=None, urgencias=None) -> list:
        from django.db.models import Case, IntegerField, Value, When
        from ..models import Publicacion
        from ..serializers import PublicacionSerializer

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

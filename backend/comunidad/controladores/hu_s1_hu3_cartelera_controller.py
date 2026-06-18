"""
Sprint 1 HU 3: Como usuario, quiero visualizar una cartelera principal
y usar filtros (por categoría, emergencias de urgencia alta o necesidades críticas).
"""


class CarteleraController:
    """Controlador para Sprint 1 HU 3 — Cartelera con filtros."""

    def __init__(self, publicacion_repository):
        self._pub_repo = publicacion_repository

    def obtener_cartelera(self, categoria=None, urgencias=None) -> list:
        qs = self._pub_repo.obtener_cartelera(categoria=categoria, urgencias=urgencias)
        
        # Serializar manualmente sin usar serializers
        return [
            {
                "id": p.id,
                "usuario": p.usuario_id,
                "usuario_nombre_real": p.usuario_nombre_real,
                "usuario_estrellas": p.usuario_promedio_estrellas,
                "tipo": p.tipo,
                "titulo": p.titulo,
                "descripcion": p.descripcion,
                "categoria": p.categoria,
                "urgencia": p.urgencia,
                "esta_activa": p.esta_activa,
                "fecha_creacion": p.fecha_creacion.isoformat() if p.fecha_creacion else None,
            }
            for p in qs
        ]

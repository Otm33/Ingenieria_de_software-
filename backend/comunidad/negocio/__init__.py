# Business logic module - Anemic Domain Model pattern
# All business logic separated from domain entities

from .usuario import (
    tiene_saldo_critico,
    puede_modificar_publicaciones,
    es_comercio_activo,
    puede_publicar,
    puede_emitir_vuelto_comercial,
    puede_pagar_con_saldo,
    es_miembro_activo,
)
from .publicacion import (
    es_talento,
    es_necesidad,
    es_urgente,
    es_critica,
    validar_reglas_negocio,
)
from .trueque import (
    esta_pendiente,
    esta_aceptado,
    esta_en_curso,
    esta_finalizado,
    ambas_partes_confirmaron,
    puede_confirmar,
    es_participante,
    contraparte,
    contraparte_id,
    es_intercambio_mutuo,
)
from .resena import (
    calificacion_valida,
    comentario_valido,
    validar,
    es_positiva,
    es_negativa,
)
from .notificacion import (
    esta_leida,
    es_de_tipo_match,
    es_de_tipo_propuesta,
)
from .trueque_multiple import (
    todos_aceptaron,
    todos_pares_confirmaron,
    esta_finalizado as trueque_multiple_esta_finalizado,
    es_participante as trueque_multiple_es_participante,
    obtener_rol,
)

__all__ = [
    # Usuario business logic
    "tiene_saldo_critico",
    "puede_modificar_publicaciones",
    "es_comercio_activo",
    "puede_publicar",
    "puede_emitir_vuelto_comercial",
    "puede_pagar_con_saldo",
    "es_miembro_activo",
    # Publicacion business logic
    "es_talento",
    "es_necesidad",
    "es_urgente",
    "es_critica",
    "validar_reglas_negocio",
    # Trueque business logic
    "esta_pendiente",
    "esta_aceptado",
    "esta_en_curso",
    "esta_finalizado",
    "ambas_partes_confirmaron",
    "puede_confirmar",
    "es_participante",
    "contraparte",
    "contraparte_id",
    "es_intercambio_mutuo",
    # Resena business logic
    "calificacion_valida",
    "comentario_valido",
    "validar",
    "es_positiva",
    "es_negativa",
    # Notificacion business logic
    "esta_leida",
    "es_de_tipo_match",
    "es_de_tipo_propuesta",
    # TruequeMultiple business logic
    "todos_aceptaron",
    "todos_pares_confirmaron",
    "trueque_multiple_esta_finalizado",
    "trueque_multiple_es_participante",
    "obtener_rol",
]

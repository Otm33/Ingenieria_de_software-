"""Migrar solicitudes al catálogo unificado de cartelera (whitelist social)."""

from django.db import migrations

from comunidad.catalogo_causas_sociales import (
    MAPEO_TITULOS_CATALOGO_ANTIGUO,
    TITULOS_CAUSA_SOCIAL_PERMITIDOS,
)


def migrar_solicitudes_catalogo(apps, schema_editor):
    SolicitudApoyoSocial = apps.get_model("comunidad", "SolicitudApoyoSocial")
    Publicacion = apps.get_model("comunidad", "Publicacion")
    titulos_validos = set(TITULOS_CAUSA_SOCIAL_PERMITIDOS)

    for solicitud in SolicitudApoyoSocial.objects.all().iterator():
        titulo_actual = solicitud.titulo
        if titulo_actual in MAPEO_TITULOS_CATALOGO_ANTIGUO:
            nuevo_titulo, nueva_categoria = MAPEO_TITULOS_CATALOGO_ANTIGUO[titulo_actual]
            solicitud.titulo = nuevo_titulo
            solicitud.categoria = nueva_categoria
            solicitud.save(update_fields=["titulo", "categoria"])
            if solicitud.publicacion_id:
                Publicacion.objects.filter(pk=solicitud.publicacion_id).update(
                    titulo=nuevo_titulo,
                    categoria=nueva_categoria,
                )
            continue

        if titulo_actual not in titulos_validos and solicitud.estado != "RECHAZADA":
            solicitud.estado = "RECHAZADA"
            solicitud.save(update_fields=["estado"])
            if solicitud.publicacion_id:
                Publicacion.objects.filter(pk=solicitud.publicacion_id).update(
                    esta_activa=False,
                )


def revertir_migracion(apps, schema_editor):
    """No reversible: títulos antiguos no se restauran automáticamente."""


class Migration(migrations.Migration):

    dependencies = [
        ("comunidad", "0015_capa2_horas_solidarias"),
    ]

    operations = [
        migrations.RunPython(migrar_solicitudes_catalogo, revertir_migracion),
    ]

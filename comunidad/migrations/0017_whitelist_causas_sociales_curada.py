"""Rechazar solicitudes con títulos fuera de la whitelist curada de causas sociales."""

from django.db import migrations

from comunidad.catalogo_causas_sociales import TITULOS_CAUSA_SOCIAL_PERMITIDOS


def rechazar_solicitudes_fuera_whitelist_curada(apps, schema_editor):
    SolicitudApoyoSocial = apps.get_model("comunidad", "SolicitudApoyoSocial")
    Publicacion = apps.get_model("comunidad", "Publicacion")
    titulos_validos = set(TITULOS_CAUSA_SOCIAL_PERMITIDOS)

    for solicitud in SolicitudApoyoSocial.objects.all().iterator():
        if solicitud.titulo in titulos_validos:
            continue

        if solicitud.estado != "RECHAZADA":
            solicitud.estado = "RECHAZADA"
            solicitud.save(update_fields=["estado"])

        if solicitud.publicacion_id:
            Publicacion.objects.filter(pk=solicitud.publicacion_id).update(
                esta_activa=False,
            )


def revertir_migracion(apps, schema_editor):
    """No reversible."""


class Migration(migrations.Migration):

    dependencies = [
        ("comunidad", "0016_migrar_catalogo_causas_sociales"),
    ]

    operations = [
        migrations.RunPython(
            rechazar_solicitudes_fuera_whitelist_curada,
            revertir_migracion,
        ),
    ]

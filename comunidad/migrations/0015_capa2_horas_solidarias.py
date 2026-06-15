import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comunidad", "0014_solicitudapoyosocial_categoria"),
    ]

    operations = [
        migrations.AddField(
            model_name="publicacion",
            name="es_causa_social",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="solicitudapoyosocial",
            name="horas_solidarias_disponibles",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="solicitudapoyosocial",
            name="horas_solidarias_utilizadas",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="solicitudapoyosocial",
            name="publicacion",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="solicitud_apoyo_social",
                to="comunidad.publicacion",
            ),
        ),
    ]

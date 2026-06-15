from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comunidad", "0013_donacion_horas_asignacion"),
    ]

    operations = [
        migrations.AddField(
            model_name="solicitudapoyosocial",
            name="categoria",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
    ]

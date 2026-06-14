from datetime import timedelta

from django.db import migrations, models
from django.utils import timezone


def asignar_fecha_expiracion_existente(apps, schema_editor):
    SaldoComercial = apps.get_model("comunidad", "SaldoComercial")
    vigencia = timedelta(days=365 * 12)
    for movimiento in SaldoComercial.objects.all():
        base = movimiento.fecha or timezone.now()
        movimiento.fecha_expiracion = base + vigencia
        movimiento.save(update_fields=["fecha_expiracion"])


class Migration(migrations.Migration):

    dependencies = [
        ("comunidad", "0009_alter_usuario_managers"),
    ]

    operations = [
        migrations.AddField(
            model_name="saldocomercial",
            name="fecha_expiracion",
            field=models.DateTimeField(null=True),
        ),
        migrations.RunPython(asignar_fecha_expiracion_existente, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="saldocomercial",
            name="fecha_expiracion",
            field=models.DateTimeField(),
        ),
    ]

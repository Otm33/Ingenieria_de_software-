from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comunidad", "0010_saldocomercial_fecha_expiracion"),
    ]

    operations = [
        migrations.AddField(
            model_name="saldocomercial",
            name="valor_producto",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name="saldocomercial",
            name="monto_recibido",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]

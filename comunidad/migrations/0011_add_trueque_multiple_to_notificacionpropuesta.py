from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("comunidad", "0010_acuerdotruequemultiple_resenamultiple"),
    ]

    operations = [
        migrations.AddField(
            model_name="notificacionpropuesta",
            name="trueque_multiple",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notificaciones_multiple', to='comunidad.acuerdotruequemultiple'),
        ),
        migrations.AlterField(
            model_name="notificacionpropuesta",
            name="trueque",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notificaciones', to='comunidad.acuerdotrueque'),
        ),
    ]

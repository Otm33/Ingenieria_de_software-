from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comunidad', '0007_remove_usuario_promedio_estrellas_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificacionpropuesta',
            name='match_detalle',
            field=models.JSONField(blank=True, null=True),
        ),
    ]

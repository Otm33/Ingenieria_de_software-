from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comunidad', '0012_impacto_social_models'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donacionhoras',
            name='tipo_destino',
            field=models.CharField(
                choices=[
                    ('CAUSA', 'Causa'),
                    ('FONDO', 'Fondo'),
                    ('ASIGNACION', 'Asignación desde fondo'),
                ],
                max_length=10,
            ),
        ),
    ]

"""
Sprint 2 HU1: Data migration que crea el usuario especial 'fondo_comunitario'.
Este usuario actúa como receptáculo del fondo de donaciones solidarias.
Nadie inicia sesión con él; tiene contraseña inutilizable.
"""
from django.db import migrations


def crear_fondo_comunitario(apps, schema_editor):
    """Crea el usuario especial del fondo comunitario si no existe."""
    Usuario = apps.get_model('comunidad', 'Usuario')

    if not Usuario.objects.filter(username='fondo_comunitario').exists():
        from django.contrib.auth.hashers import make_password
        Usuario.objects.create(
            username='fondo_comunitario',
            email='fondo@tutrueque.com',
            nombre_real='Fondo Comunitario TuTrueque',
            horas_de_vida=0.0,
            es_comercio=False,
            es_fondo_comunitario=True,
            estado_social='NINGUNO',
            is_active=True,
            is_staff=False,
            is_superuser=False,
            # Contraseña inutilizable: nadie puede iniciar sesión con este usuario
            password=make_password(None),
        )
        print("Usuario 'fondo_comunitario' creado exitosamente.")
    else:
        # Si ya existe, aseguramos que tenga es_fondo_comunitario=True
        Usuario.objects.filter(username='fondo_comunitario').update(es_fondo_comunitario=True)
        print("Usuario 'fondo_comunitario' ya existe — verificado.")


class Migration(migrations.Migration):
    dependencies = [
        ('comunidad', '0014_sprint2_hu1_impacto_social'),
    ]

    operations = [
        migrations.RunPython(crear_fondo_comunitario, migrations.RunPython.noop),
    ]

from django.db import migrations

def ensure_admin_permissions(apps, schema_editor):
    """Asegura que el usuario admin tenga permisos de administrador."""
    Usuario = apps.get_model('comunidad', 'Usuario')
    
    try:
        admin_user = Usuario.objects.get(username='admin')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()
        print("Usuario admin configurado con permisos de administrador")
    except Usuario.DoesNotExist:
        print("El usuario admin no existe")

class Migration(migrations.Migration):
    dependencies = [
        ('comunidad', '0011_add_trueque_multiple_to_notificacionpropuesta'),
    ]

    operations = [
        migrations.RunPython(ensure_admin_permissions),
    ]

#!/usr/bin/env python
"""Script para configurar el usuario admin con permisos de staff y superuser."""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from comunidad.models import Usuario

def configurar_admin(username=None):
    """Configura el usuario admin con permisos de staff y superuser."""
    if not username:
        username = input("Ingrese el nombre de usuario del admin: ")
    
    try:
        usuario = Usuario.objects.get(username=username)
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.save()
        print(f"✅ Usuario '{username}' configurado como admin exitosamente.")
        print(f"   is_staff: {usuario.is_staff}")
        print(f"   is_superuser: {usuario.is_superuser}")
    except Usuario.DoesNotExist:
        print(f"❌ Error: El usuario '{username}' no existe.")
    except Exception as e:
        print(f"❌ Error al configurar admin: {str(e)}")

if __name__ == "__main__":
    import sys
    username = sys.argv[1] if len(sys.argv) > 1 else None
    configurar_admin(username)

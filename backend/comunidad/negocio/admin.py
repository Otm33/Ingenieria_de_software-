"""
Capa de Negocio — Reglas de administracion (Sprint 2 HU3).

Funciones puras que validan permisos y restricciones administrativas.
No dependen de Django ni de ningun framework.

Llamado desde:
    ``services/admin_panel.py`` -> ``AdminPanelService``
"""


def validar_es_administrador(usuario):
    """Verifica que el usuario sea staff o superusuario. Lanza ValueError si no."""
    if not (getattr(usuario, 'is_staff', False) or getattr(usuario, 'is_superuser', False)):
        raise ValueError('No tienes permisos de administrador.')


def validar_puede_eliminar_usuario(admin_id, usuario_id):
    """Un administrador no puede eliminarse a si mismo."""
    if int(admin_id) == int(usuario_id):
        raise ValueError('No puedes eliminar tu propia cuenta de administrador.')


def validar_puede_cambiar_rol(admin):
    """Solo superusuarios pueden promover/degradar staff."""
    if not getattr(admin, 'is_superuser', False):
        raise ValueError('Solo un superusuario puede cambiar roles de staff.')


def validar_busqueda(termino):
    """Sanitiza y valida el termino de busqueda. Retorna el termino limpio o None."""
    if not termino:
        return None
    termino = str(termino).strip()
    if len(termino) > 100:
        raise ValueError('El termino de busqueda no puede exceder 100 caracteres.')
    return termino if termino else None

import random
import string


def generar_codigo_confirmacion(trueque_repository=None):
    """Genera un código alfanumérico único de 8 caracteres.

    Args:
        trueque_repository: repositorio con método existe_codigo_confirmacion().
            Si no se provee, genera el código sin verificar unicidad en BD.
    """
    caracteres = string.ascii_uppercase + string.digits
    while True:
        codigo = ''.join(random.choice(caracteres) for _ in range(8))
        if trueque_repository is None:
            return codigo
        if not trueque_repository.existe_codigo_confirmacion(codigo):
            return codigo


CATEGORIAS_PUBLICACION = {
    "Mantenimiento, Reparaciones y Construcción",
    "Tecnología, Desarrollo y Redes",
    "Limpieza, Organización y Hogar",
    "Diseño, Multimedia y Arte",
    "Redacción, Traducción y Contenidos",
    "Educación, Asesoría y Tutorías",
    "Automotriz, Transporte y Logística",
    "Eventos, Ocio y Entretenimiento",
    "Cuidado de la Salud, Bienestar y Terapias",
}


class BusinessError(Exception):
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

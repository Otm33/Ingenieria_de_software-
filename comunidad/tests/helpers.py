"""Helpers compartidos para pruebas de HU4 (Emparejamiento y Gestión de Acuerdos)."""

from comunidad.models import AcuerdoTrueque, Publicacion, Resena, Usuario

CATEGORIA_MANTENIMIENTO = "Mantenimiento, Reparaciones y Construcción"
TITULO_INSTALACION_ELECTRICA = "Instalación eléctrica"
TITULO_FONTANERIA_GENERAL = "Fontanería general"


def crear_usuario(username, email, nombre_real, horas=0.0, **kwargs):
    """Crea un usuario de prueba con contraseña fija."""
    return Usuario.objects.create_user(
        username=username,
        email=email,
        password="testpass123",
        nombre_real=nombre_real,
        horas_de_vida=horas,
        **kwargs,
    )


def crear_publicacion(
    usuario,
    tipo,
    titulo,
    categoria,
    descripcion="Descripción de prueba para HU4.",
    urgencia="NORMAL",
    esta_activa=True,
):
    """Crea una publicación activa asociada al usuario."""
    return Publicacion.objects.create(
        usuario=usuario,
        tipo=tipo,
        titulo=titulo,
        descripcion=descripcion,
        categoria=categoria,
        urgencia=urgencia,
        esta_activa=esta_activa,
    )


def crear_trueque(emisor, receptor, estado="FINALIZADO", **kwargs):
    """Crea un acuerdo de trueque entre dos usuarios."""
    return AcuerdoTrueque.objects.create(
        emisor=emisor,
        receptor=receptor,
        estado=estado,
        **kwargs,
    )


def crear_resena(trueque, calificador, calificado, estrellas, comentario="Reseña de prueba."):
    """Crea una reseña asociada a un trueque."""
    return Resena.objects.create(
        trueque=trueque,
        calificador=calificador,
        calificado=calificado,
        estrellas=estrellas,
        comentario=comentario,
    )

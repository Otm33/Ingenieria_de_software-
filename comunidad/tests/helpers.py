"""Helpers compartidos para pruebas de HU4 (Emparejamiento y Gestión de Acuerdos)."""

from decimal import Decimal

from comunidad.models import AcuerdoTrueque, Publicacion, Resena, Usuario

CATEGORIA_MANTENIMIENTO = "Mantenimiento, Reparaciones y Construcción"
TITULO_INSTALACION_ELECTRICA = "Instalación eléctrica"
TITULO_FONTANERIA_GENERAL = "Fontanería general"

CATEGORIA_CAUSA_SOCIAL_EJEMPLO = "Cuidado de la Salud, Bienestar y Terapias"
TITULO_CAUSA_SOCIAL_EJEMPLO = "Cuidado de abuelos"
CATEGORIA_EDUCACION_CAUSA_SOCIAL = "Educación, Asesoría y Tutorías"
TITULO_APOYO_ESCOLAR_PRIMARIA = "Apoyo escolar primaria"
CATEGORIA_TRANSPORTE_CAUSA_SOCIAL = "Automotriz, Transporte y Logística"
TITULO_CONDUCTOR_REEMPLAZO = "Conductor de reemplazo"


def datos_solicitud_social_validos(**overrides):
    """Payload válido para crear solicitudes de apoyo social."""
    datos = {
        "categoria": CATEGORIA_CAUSA_SOCIAL_EJEMPLO,
        "titulo": TITULO_CAUSA_SOCIAL_EJEMPLO,
        "descripcion": "Descripción de apoyo social.",
    }
    datos.update(overrides)
    return datos


def marcar_vulnerable(usuario):
    # Usar solo cuando el test necesite usuario ya vulnerable SIN pasar por aprobación
    # (ej. asignación desde fondo). Para flujo publicar→aprobar, NO marcar antes.
    usuario.estado_social = "VULNERABLE"
    usuario.save(update_fields=["estado_social"])
    return usuario


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


def crear_comercio(username, email, nombre_real, saldo=Decimal("0.00"), **kwargs):
    """Crea un comercio activo con saldo comercial inicial."""
    return crear_usuario(
        username,
        email,
        nombre_real,
        es_comercio=True,
        saldo_comercial=saldo,
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

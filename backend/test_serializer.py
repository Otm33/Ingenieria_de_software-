import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")
django.setup()

from backend.comunidad.models import Usuario, Publicacion, NotificacionPropuesta
from backend.comunidad.serializers import NotificacionSerializer

def test_serializer():
    u1 = Usuario.objects.first()
    u2 = Usuario.objects.exclude(id=u1.id).first()
    
    # Notificacion Normal
    n1 = NotificacionPropuesta.objects.filter(tipo="MATCH").first()
    if n1:
        print("Serializando Notificacion MATCH:")
        try:
            print(NotificacionSerializer(n1).data)
        except Exception as e:
            print("ERROR IN MATCH:", e)

    # Notificacion Multiple
    n2 = NotificacionPropuesta.objects.filter(trueque_multiple__isnull=False).first()
    if n2:
        print("Serializando Notificacion MULTIPLE:")
        try:
            print(NotificacionSerializer(n2).data)
        except Exception as e:
            print("ERROR IN MULTIPLE:", e)
    else:
        # Create a fake one to test
        n3 = NotificacionPropuesta(
            destinatario=u1,
            remitente=u2,
            tipo="PROPUESTA",
            mensaje="Test",
            # no trueque!
            # no publicacion_original!
        )
        print("Serializando Notificacion Falsa (sin trueque ni publicacion):")
        try:
            print(NotificacionSerializer(n3).data)
        except Exception as e:
            print("ERROR IN FAKE MULTIPLE:", e)

if __name__ == "__main__":
    test_serializer()

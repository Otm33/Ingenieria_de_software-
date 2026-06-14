import os
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from comunidad.tests.helpers import crear_usuario, crear_publicacion
from django.conf import settings

# Allow testserver host for APIClient requests
settings.ALLOWED_HOSTS = list(getattr(settings, 'ALLOWED_HOSTS', [])) + ['testserver', 'localhost', '127.0.0.1']

try:
    import uuid
    suffix = uuid.uuid4().hex[:6]
    user_a = crear_usuario(f'dbg_a_{suffix}', f'dbg_a_{suffix}@test.com', 'dbg a', horas=0.0)
    user_b = crear_usuario(f'dbg_b_{suffix}', f'dbg_b_{suffix}@test.com', 'dbg b', horas=5.0)
    # Crear un flujo completo TALENTO->NECESIDAD que la API debe manejar
    pub_talento_a = crear_publicacion(user_a, 'TALENTO', 'Talento A', 'Mantenimiento')
    pub_necesidad_b = crear_publicacion(user_b, 'NECESIDAD', 'Necesidad B', 'Mantenimiento')

    client = APIClient()
    client.force_authenticate(user=user_a)
    crear_resp = client.post('/api/trueques/propuestas/crear/', {
        'receptor_id': user_b.id,
        'publicacion_emisor_id': pub_talento_a.id,
        'publicacion_receptor_id': pub_necesidad_b.id,
    }, format='json')

    print('CREAR STATUS:', crear_resp.status_code)
    print('CREAR DATA:', getattr(crear_resp, 'data', crear_resp.content))

    trueque_id = crear_resp.data.get('propuesta_id')

    # Receptor acepta
    client.force_authenticate(user=user_b)
    aceptar_resp = client.post(f'/api/trueques/{trueque_id}/responder/', {'accion': 'ACEPTAR'}, format='json')
    print('ACEPTAR STATUS:', aceptar_resp.status_code)
    print('ACEPTAR DATA:', getattr(aceptar_resp, 'data', aceptar_resp.content))

    # Emisor finaliza (primera confirmación)
    client.force_authenticate(user=user_a)
    finalizar_resp = client.post(f'/api/trueques/{trueque_id}/finalizar/')
    print('FINALIZAR STATUS:', finalizar_resp.status_code)
    print('FINALIZAR DATA:', getattr(finalizar_resp, 'data', finalizar_resp.content))

    print('STATUS:', response.status_code)
    try:
        print('DATA:', response.data)
    except Exception:
        print('No JSON data; content:', response.content)

except Exception:
    traceback.print_exc()

from django.test import TestCase, override_settings

from ..helpers import crear_usuario, crear_publicacion, CATEGORIA_MANTENIMIENTO
from ..services.matchmaking_multiple import MatchmakingMultipleService
from ..models import AcuerdoTruequeMultiple


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class TruequeMultipleTests(TestCase):
    def test_detectar_y_crear_trueque_multiple_3_usuarios(self):
        # Crear 3 usuarios A, B, C que formen un ciclo A->B->C->A
        user_a = crear_usuario("tm_a", "a@tm.com", "User A")
        user_b = crear_usuario("tm_b", "b@tm.com", "User B")
        user_c = crear_usuario("tm_c", "c@tm.com", "User C")

        # A tiene talento X y necesidad Z
        crear_publicacion(user_a, "TALENTO", "X", CATEGORIA_MANTENIMIENTO)
        crear_publicacion(user_a, "NECESIDAD", "Z", CATEGORIA_MANTENIMIENTO)

        # B tiene talento Y y necesidad X
        crear_publicacion(user_b, "TALENTO", "Y", CATEGORIA_MANTENIMIENTO)
        crear_publicacion(user_b, "NECESIDAD", "X", CATEGORIA_MANTENIMIENTO)

        # C tiene talento Z and necesidad Y
        crear_publicacion(user_c, "TALENTO", "Z", CATEGORIA_MANTENIMIENTO)
        crear_publicacion(user_c, "NECESIDAD", "Y", CATEGORIA_MANTENIMIENTO)

        servicio = MatchmakingMultipleService()
        propuestas = servicio.detectar_y_notificar_ciclos(user_a)

        # Debería haberse creado al menos un AcuerdoTruequeMultiple en estado PENDIENTE
        trueques = AcuerdoTruequeMultiple.objects.filter(estado="PENDIENTE")
        self.assertTrue(trueques.exists())
        self.assertGreaterEqual(len(propuestas), 1)

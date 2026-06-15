"""Pruebas API HU4 — Fase 3."""

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from ..helpers import (
    CATEGORIA_MANTENIMIENTO,
    TITULO_FONTANERIA_GENERAL,
    TITULO_INSTALACION_ELECTRICA,
    crear_publicacion,
    crear_usuario,
)
from ..services import MatchmakingService


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class HU4APITestCase(APITestCase):
    """Base para pruebas API HU4."""

    def setUp(self):
        self.client = APIClient()

    def _crear_par_complementario(self):
        user_a = crear_usuario("api_user_a", "api_a@test.com", "API User A", horas=0.0)
        user_b = crear_usuario("api_user_b", "api_b@test.com", "API User B", horas=5.0)
        pub_talento_a = crear_publicacion(
            user_a, "TALENTO", TITULO_INSTALACION_ELECTRICA, CATEGORIA_MANTENIMIENTO
        )
        pub_necesidad_a = crear_publicacion(
            user_a, "NECESIDAD", TITULO_FONTANERIA_GENERAL, CATEGORIA_MANTENIMIENTO
        )
        pub_talento_b = crear_publicacion(
            user_b, "TALENTO", TITULO_FONTANERIA_GENERAL, CATEGORIA_MANTENIMIENTO
        )
        pub_necesidad_b = crear_publicacion(
            user_b, "NECESIDAD", TITULO_INSTALACION_ELECTRICA, CATEGORIA_MANTENIMIENTO
        )
        return {
            "user_a": user_a,
            "user_b": user_b,
            "pub_talento_a": pub_talento_a,
            "pub_necesidad_a": pub_necesidad_a,
            "pub_talento_b": pub_talento_b,
            "pub_necesidad_b": pub_necesidad_b,
        }


class APIHU4Tests(HU4APITestCase):
    def test_api_matchmaking_retorna_matches_enriquecidos(self):
        datos = self._crear_par_complementario()
        self.client.force_authenticate(user=datos["user_a"])

        response = self.client.get("/api/matchmaking/")

        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["cantidad"], 1)
        match = response.data["matches"][0]
        self.assertEqual(match["usuario"]["id"], datos["user_b"].id)
        self.assertIn("talentos_coincidentes", match)
        self.assertIn("necesidades_coincidentes", match)
        self.assertIn("publicaciones_sugeridas", match)
        self.assertTrue(match["talentos_coincidentes"])

    def test_api_crear_propuesta_necesidad_necesidad_400(self):
        datos = self._crear_par_complementario()
        self.client.force_authenticate(user=datos["user_a"])

        response = self.client.post(
            "/api/trueques/propuestas/crear/",
            {
                "receptor_id": datos["user_b"].id,
                "publicacion_emisor_id": datos["pub_necesidad_a"].id,
                "publicacion_receptor_id": datos["pub_necesidad_b"].id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("necesidades", response.data["error"].lower())

    def test_api_crear_propuesta_201(self):
        datos = self._crear_par_complementario()
        self.client.force_authenticate(user=datos["user_a"])

        response = self.client.post(
            "/api/trueques/propuestas/crear/",
            {
                "receptor_id": datos["user_b"].id,
                "publicacion_emisor_id": datos["pub_talento_a"].id,
                "publicacion_receptor_id": datos["pub_necesidad_b"].id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("propuesta_id", response.data)

    def test_api_responder_aceptar(self):
        datos = self._crear_par_complementario()
        self.client.force_authenticate(user=datos["user_a"])
        crear = self.client.post(
            "/api/trueques/propuestas/crear/",
            {
                "receptor_id": datos["user_b"].id,
                "publicacion_emisor_id": datos["pub_talento_a"].id,
                "publicacion_receptor_id": datos["pub_necesidad_b"].id,
            },
            format="json",
        )
        trueque_id = crear.data["propuesta_id"]

        self.client.force_authenticate(user=datos["user_b"])
        response = self.client.post(
            f"/api/trueques/{trueque_id}/responder/",
            {"accion": "ACEPTAR"},
            format="json",
        )

        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=datos["user_a"])
        mis_trueques = self.client.get("/api/mis-trueques/")
        trueque = mis_trueques.data["trueques"][0]
        self.assertEqual(trueque["estado"], "EN_CURSO")

    def test_api_finalizar_primera_confirmacion_200_sin_transferencia(self):
        datos = self._crear_par_complementario()
        self.client.force_authenticate(user=datos["user_a"])
        crear = self.client.post(
            "/api/trueques/propuestas/crear/",
            {
                "receptor_id": datos["user_b"].id,
                "publicacion_emisor_id": datos["pub_talento_a"].id,
                "publicacion_receptor_id": datos["pub_necesidad_b"].id,
            },
            format="json",
        )
        trueque_id = crear.data["propuesta_id"]

        self.client.force_authenticate(user=datos["user_b"])
        self.client.post(
            f"/api/trueques/{trueque_id}/responder/",
            {"accion": "ACEPTAR"},
            format="json",
        )

        self.client.force_authenticate(user=datos["user_a"])
        response = self.client.post(f"/api/trueques/{trueque_id}/finalizar/")

        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["saldo_transferido"])
        self.assertTrue(response.data["emisor_confirmado"])
        self.assertFalse(response.data["receptor_confirmado"])
        self.assertEqual(response.data["estado"], "EN_CURSO")

        datos["user_a"].refresh_from_db()
        datos["user_b"].refresh_from_db()
        self.assertEqual(datos["user_a"].horas_de_vida, 0.0)
        self.assertEqual(datos["user_b"].horas_de_vida, 5.0)

    def test_api_finalizar_segunda_confirmacion_transfiere(self):
        datos = self._crear_par_complementario()
        self.client.force_authenticate(user=datos["user_a"])
        crear = self.client.post(
            "/api/trueques/propuestas/crear/",
            {
                "receptor_id": datos["user_b"].id,
                "publicacion_emisor_id": datos["pub_talento_a"].id,
                "publicacion_receptor_id": datos["pub_necesidad_b"].id,
            },
            format="json",
        )
        trueque_id = crear.data["propuesta_id"]

        self.client.force_authenticate(user=datos["user_b"])
        self.client.post(
            f"/api/trueques/{trueque_id}/responder/",
            {"accion": "ACEPTAR"},
            format="json",
        )

        self.client.force_authenticate(user=datos["user_a"])
        self.client.post(f"/api/trueques/{trueque_id}/finalizar/")

        self.client.force_authenticate(user=datos["user_b"])
        response = self.client.post(f"/api/trueques/{trueque_id}/finalizar/")

        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["saldo_transferido"])
        self.assertTrue(response.data["habilitar_resena"])
        self.assertEqual(response.data["estado"], "FINALIZADO")

        datos["user_a"].refresh_from_db()
        datos["user_b"].refresh_from_db()
        self.assertEqual(datos["user_a"].horas_de_vida, 1.0)
        self.assertEqual(datos["user_b"].horas_de_vida, 4.0)

    def test_api_mis_trueques_lista_acuerdos(self):
        datos = self._crear_par_complementario()
        self.client.force_authenticate(user=datos["user_a"])
        self.client.post(
            "/api/trueques/propuestas/crear/",
            {
                "receptor_id": datos["user_b"].id,
                "publicacion_emisor_id": datos["pub_talento_a"].id,
                "publicacion_receptor_id": datos["pub_necesidad_b"].id,
            },
            format="json",
        )

        response = self.client.get("/api/mis-trueques/")

        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["cantidad"], 1)
        trueque = response.data["trueques"][0]
        self.assertIn("emisor_nombre", trueque)
        self.assertIn("receptor_nombre", trueque)
        self.assertIn("publicacion_emisor", trueque)
        self.assertIn("puede_confirmar", trueque)

    def test_api_registrar_resena_actualiza_promedio_en_respuesta_perfil(self):
        datos = self._crear_par_complementario()
        self.client.force_authenticate(user=datos["user_a"])
        crear = self.client.post(
            "/api/trueques/propuestas/crear/",
            {
                "receptor_id": datos["user_b"].id,
                "publicacion_emisor_id": datos["pub_talento_a"].id,
                "publicacion_receptor_id": datos["pub_necesidad_b"].id,
            },
            format="json",
        )
        trueque_id = crear.data["propuesta_id"]

        self.client.force_authenticate(user=datos["user_b"])
        self.client.post(
            f"/api/trueques/{trueque_id}/responder/",
            {"accion": "ACEPTAR"},
            format="json",
        )
        self.client.post(f"/api/trueques/{trueque_id}/finalizar/")

        self.client.force_authenticate(user=datos["user_a"])
        self.client.post(f"/api/trueques/{trueque_id}/finalizar/")

        self.client.post(
            "/api/resenas/",
            {"trueque_id": trueque_id, "estrellas": 4, "comentario": "Muy buen trabajo."},
            format="json",
        )
        self.client.force_authenticate(user=datos["user_b"])
        self.client.post(
            "/api/resenas/",
            {"trueque_id": trueque_id, "estrellas": 2, "comentario": "Regular."},
            format="json",
        )

        self.client.force_authenticate(user=datos["user_a"])
        perfil = self.client.get(f"/api/perfil/{datos['user_a'].id}/")

        self.assertEqual(perfil.status_code, status.HTTP_200_OK)
        self.assertEqual(perfil.data["promedio_estrellas"], 2.0)
        self.assertEqual(perfil.data["usuario"]["promedio_estrellas"], 2.0)

    def test_api_mi_perfil_devuelve_cantidad_resenas_y_calificador_username(self):
        datos = self._crear_par_complementario()
        self.client.force_authenticate(user=datos["user_a"])
        crear = self.client.post(
            "/api/trueques/propuestas/crear/",
            {
                "receptor_id": datos["user_b"].id,
                "publicacion_emisor_id": datos["pub_talento_a"].id,
                "publicacion_receptor_id": datos["pub_necesidad_b"].id,
            },
            format="json",
        )
        trueque_id = crear.data["propuesta_id"]

        self.client.force_authenticate(user=datos["user_b"])
        self.client.post(
            f"/api/trueques/{trueque_id}/responder/",
            {"accion": "ACEPTAR"},
            format="json",
        )
        self.client.post(f"/api/trueques/{trueque_id}/finalizar/")

        self.client.force_authenticate(user=datos["user_a"])
        self.client.post(f"/api/trueques/{trueque_id}/finalizar/")

        self.client.post(
            "/api/resenas/",
            {"trueque_id": trueque_id, "estrellas": 4, "comentario": "Muy buen trabajo."},
            format="json",
        )
        self.client.force_authenticate(user=datos["user_b"])
        self.client.post(
            "/api/resenas/",
            {"trueque_id": trueque_id, "estrellas": 2, "comentario": "Regular."},
            format="json",
        )

        self.client.force_authenticate(user=datos["user_a"])
        mi_perfil = self.client.get("/api/mi-perfil/")

        self.assertEqual(mi_perfil.status_code, status.HTTP_200_OK)
        self.assertEqual(mi_perfil.data["cantidad_resenas"], 1)
        self.assertEqual(mi_perfil.data["promedio_estrellas"], 2.0)
        self.assertEqual(mi_perfil.data["usuario"]["promedio_estrellas"], 2.0)
        self.assertEqual(len(mi_perfil.data["resenas_recibidas"]), 1)

        resena = mi_perfil.data["resenas_recibidas"][0]
        self.assertEqual(resena["calificador_username"], datos["user_b"].username)
        self.assertEqual(resena["calificador_nombre"], datos["user_b"].nombre_real)
        self.assertEqual(resena["estrellas"], 2)

    def test_api_notificaciones_match_detalle(self):
        datos = self._crear_par_complementario()
        MatchmakingService().detectar_y_notificar_matches(datos["user_a"])

        self.client.force_authenticate(user=datos["user_a"])
        response = self.client.get("/api/notificaciones/")

        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        match_notif = next(
            notif for notif in response.data["notificaciones"] if notif["tipo"] == "MATCH"
        )
        self.assertIn("match_detalle", match_notif)
        self.assertEqual(len(match_notif["match_detalle"]), 2)

        roles = {entrada["rol"] for entrada in match_notif["match_detalle"]}
        self.assertEqual(roles, {"recibo", "doy"})

        recibo = next(
            entrada for entrada in match_notif["match_detalle"] if entrada["rol"] == "recibo"
        )
        doy = next(entrada for entrada in match_notif["match_detalle"] if entrada["rol"] == "doy")
        self.assertEqual(recibo["mi_titulo"], TITULO_FONTANERIA_GENERAL)
        self.assertEqual(doy["mi_titulo"], TITULO_INSTALACION_ELECTRICA)

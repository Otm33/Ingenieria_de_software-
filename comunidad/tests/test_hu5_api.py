"""Pruebas API HU5 — Red Comercial."""

from decimal import Decimal

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from comunidad.models import Usuario, UsuarioAutorizado
from comunidad.tests.helpers import (
    CATEGORIA_MANTENIMIENTO,
    TITULO_INSTALACION_ELECTRICA,
    crear_comercio,
    crear_usuario,
)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class HU5APITestCase(APITestCase):
    """Base para pruebas API HU5."""

    def setUp(self):
        self.client = APIClient()


class APIHU5Tests(HU5APITestCase):
    def test_api_get_comercios_requiere_auth(self):
        response = self.client.get("/api/comercios/")

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_api_get_comercios_lista_solo_comercios_activos(self):
        comercio = crear_comercio("api_com", "api_com@test.com", "Comercio API")
        usuario_normal = crear_usuario("api_user", "api_user@test.com", "Usuario API")

        self.client.force_authenticate(user=usuario_normal)
        response = self.client.get("/api/comercios/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in response.data}
        nombres = {item["nombre_real"] for item in response.data}

        self.assertIn(comercio.id, ids)
        self.assertIn("Comercio API", nombres)
        self.assertNotIn(usuario_normal.id, ids)

    def test_api_emitir_vuelto_comercio_ok(self):
        comercio = crear_comercio("api_emit", "api_emit@test.com", "Comercio Emisor")
        cliente = crear_usuario("api_cli_emit", "api_cli_emit@test.com", "Cliente Emisor")

        self.client.force_authenticate(user=comercio)
        response = self.client.post(
            "/api/comercio/emitir-vuelto/",
            {"cliente_id": cliente.id, "monto_excedente": "4.50"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("comprobante", response.data)
        self.assertIsNotNone(response.data["comprobante"])
        self.assertEqual(response.data["comprobante"]["tipo_movimiento"], "EMISION")

    def test_api_emitir_vuelto_con_valor_y_recibido_ok(self):
        comercio = crear_comercio("api_valor", "api_valor@test.com", "Comercio Valor")
        cliente = crear_usuario("api_cli_valor", "api_cli_valor@test.com", "Cliente Valor")

        self.client.force_authenticate(user=comercio)
        response = self.client.post(
            "/api/comercio/emitir-vuelto/",
            {
                "cliente_id": cliente.id,
                "valor_producto": "5.00",
                "monto_recibido": "10.00",
                "monto_excedente": "5.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comprobante = response.data["comprobante"]
        self.assertEqual(comprobante["valor_producto"], "5.00")
        self.assertEqual(comprobante["monto_recibido"], "10.00")
        self.assertEqual(comprobante["monto_excedente"], "5.00")

    def test_api_comercio_no_puede_pagar_con_saldo(self):
        comercio = crear_comercio("api_com_pago", "api_com_pago@test.com", "Comercio Sin Pago")
        comercio_destino = crear_comercio("api_com_dest", "api_com_dest@test.com", "Comercio Destino")

        self.client.force_authenticate(user=comercio)
        response = self.client.post(
            "/api/comercio/pagar/",
            {"comercio_id": comercio_destino.id, "monto": "1.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("no pueden pagar", response.data["error"].lower())

    def test_api_emitir_vuelto_usuario_normal_403(self):
        usuario_normal = crear_usuario("api_normal", "api_normal@test.com", "Usuario Normal")
        cliente = crear_usuario("api_cli_403", "api_cli_403@test.com", "Cliente 403")

        self.client.force_authenticate(user=usuario_normal)
        response = self.client.post(
            "/api/comercio/emitir-vuelto/",
            {"cliente_id": cliente.id, "monto_excedente": "1.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_pagar_con_saldo_ok(self):
        comercio_a = crear_comercio("api_pa", "api_pa@test.com", "Comercio A Pago")
        comercio_b = crear_comercio("api_pb", "api_pb@test.com", "Comercio B Pago")
        cliente = crear_usuario("api_cli_pago", "api_cli_pago@test.com", "Cliente Pago")

        self.client.force_authenticate(user=comercio_a)
        self.client.post(
            "/api/comercio/emitir-vuelto/",
            {"cliente_id": cliente.id, "monto_excedente": "4.50"},
            format="json",
        )

        self.client.force_authenticate(user=cliente)
        response = self.client.post(
            "/api/comercio/pagar/",
            {"comercio_id": comercio_b.id, "monto": "3.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("comprobante", response.data)
        self.assertEqual(response.data["saldo_restante"], 1.5)
        self.assertEqual(response.data["saldo_comercio"], 3.0)

    def test_api_pagar_saldo_insuficiente_400(self):
        comercio_b = crear_comercio("api_pinsuf", "api_pinsuf@test.com", "Comercio Insuf API")
        cliente = crear_usuario(
            "api_cli_insuf",
            "api_cli_insuf@test.com",
            "Cliente Insuf API",
            saldo_comercial=Decimal("1.00"),
        )

        self.client.force_authenticate(user=cliente)
        response = self.client.post(
            "/api/comercio/pagar/",
            {"comercio_id": comercio_b.id, "monto": "5.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("insuficiente", response.data["error"].lower())

    def test_api_mi_saldo_comercial(self):
        comercio = crear_comercio("api_saldo_com", "api_saldo_com@test.com", "Comercio Saldo")
        cliente = crear_usuario("api_saldo_cli", "api_saldo_cli@test.com", "Cliente Saldo")

        self.client.force_authenticate(user=comercio)
        self.client.post(
            "/api/comercio/emitir-vuelto/",
            {"cliente_id": cliente.id, "monto_excedente": "2.50"},
            format="json",
        )

        self.client.force_authenticate(user=cliente)
        response = self.client.get("/api/mi-saldo-comercial/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["saldo_actual"], 2.5)
        self.assertEqual(len(response.data["movimientos_como_cliente"]), 1)
        self.assertFalse(response.data["es_comercio"])


class RegistroComercioAPIHU5Tests(HU5APITestCase):
    def test_api_registro_comercio_sin_login_previo(self):
        email = "api_reg_com@test.com"
        UsuarioAutorizado.objects.guardar_email(email, "COMERCIO")

        response = self.client.post(
            "/api/registro/",
            {
                "email": email,
                "username": "api_reg_com",
                "password": "testpass123",
                "nombre_real": "Comercio API Registro",
                "es_comercio": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["es_comercio"])

        comercio = Usuario.objects.get(pk=response.data["id"])
        self.client.force_authenticate(user=comercio)

        catalogo = self.client.get("/api/comercios/")
        self.assertEqual(catalogo.status_code, status.HTTP_200_OK)
        nombres = {item["nombre_real"] for item in catalogo.data}
        self.assertIn("Comercio API Registro", nombres)

        mis_publicaciones = self.client.get("/api/mis-publicaciones/")
        self.assertEqual(mis_publicaciones.status_code, status.HTTP_200_OK)
        self.assertEqual(mis_publicaciones.data["cantidad"], 0)
        self.assertEqual(len(mis_publicaciones.data["publicaciones"]), 0)

    def test_api_registro_vecino_crea_usuario_sin_es_comercio(self):
        email = "api_reg_vec@test.com"
        UsuarioAutorizado.objects.guardar_email(email, "USUARIO")

        response = self.client.post(
            "/api/registro/",
            {
                "email": email,
                "username": "api_reg_vec",
                "password": "testpass123",
                "nombre_real": "Vecino API Registro",
                "es_comercio": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data["es_comercio"])


class ListadoClientesAPIHU5Tests(HU5APITestCase):
    def test_api_get_clientes_comercio_ok(self):
        comercio = crear_comercio("api_cli_com", "api_cli_com@test.com", "Comercio Clientes")
        vecino = crear_usuario("api_cli_vec", "api_cli_vec@test.com", "Vecino Clientes")
        crear_comercio("api_cli_otro", "api_cli_otro@test.com", "Otro Comercio")

        self.client.force_authenticate(user=comercio)
        response = self.client.get("/api/clientes/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {item["id"] for item in response.data}
        usernames = {item["username"] for item in response.data}

        self.assertIn(vecino.id, ids)
        self.assertIn("api_cli_vec", usernames)
        self.assertNotIn(comercio.id, ids)

        primer_cliente = response.data[0]
        self.assertIn("id", primer_cliente)
        self.assertIn("nombre_real", primer_cliente)
        self.assertIn("username", primer_cliente)
        self.assertNotIn("email", primer_cliente)

    def test_api_get_clientes_vecino_403(self):
        vecino = crear_usuario("api_vec_cli", "api_vec_cli@test.com", "Vecino Sin Acceso")

        self.client.force_authenticate(user=vecino)
        response = self.client.get("/api/clientes/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Solo comercios pueden consultar", response.data["error"])

    def test_api_get_clientes_requiere_auth(self):
        response = self.client.get("/api/clientes/")

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class RolComercioAPIHU5Tests(HU5APITestCase):
    def test_api_comercio_post_publicacion_403(self):
        comercio = crear_comercio("api_com_pub", "api_com_pub@test.com", "Comercio API Pub")

        self.client.force_authenticate(user=comercio)
        response = self.client.post(
            "/api/publicaciones/",
            {
                "tipo": "TALENTO",
                "titulo": TITULO_INSTALACION_ELECTRICA,
                "descripcion": "Intento de publicacion comercial",
                "categoria": CATEGORIA_MANTENIMIENTO,
                "urgencia": "NORMAL",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("no pueden publicar", response.data["error"].lower())

    def test_api_vecino_post_publicacion_201_o_200(self):
        vecino = crear_usuario("api_vec_pub", "api_vec_pub@test.com", "Vecino API Pub")

        self.client.force_authenticate(user=vecino)
        response = self.client.post(
            "/api/publicaciones/",
            {
                "tipo": "TALENTO",
                "titulo": TITULO_INSTALACION_ELECTRICA,
                "descripcion": "Publicacion valida de vecino",
                "categoria": CATEGORIA_MANTENIMIENTO,
                "urgencia": "NORMAL",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tipo"], "TALENTO")
        self.assertEqual(response.data["usuario"], vecino.id)


class CSRFRedComercialTests(HU5APITestCase):
    def _login_usuario(self, usuario, password="testpass123"):
        usuario.set_password(password)
        usuario.save()
        self.client = APIClient(enforce_csrf_checks=True)
        logged = self.client.login(username=usuario.username, password=password)
        self.assertTrue(logged)

    def test_api_emitir_vuelto_con_sesion_sin_csrf_token_ok(self):
        comercio = crear_comercio("panaderia_emit", "panaderia_emit@test.com", "Panaderia Emit")
        cliente = crear_usuario("oscar_a", "oscar_a@test.com", "Oscar A")

        self._login_usuario(comercio)
        response = self.client.post(
            "/api/comercio/emitir-vuelto/",
            {"cliente_id": cliente.id, "monto_excedente": "1.50"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("comprobante", response.data)
        self.assertNotIn("csrf", str(response.data).lower())

    def test_api_pagar_con_saldo_con_sesion_sin_csrf_token_ok(self):
        from uuid import uuid4

        uid = uuid4().hex[:8]
        comercio_a = crear_comercio(f"com_a_{uid}", f"com_a_{uid}@test.com", "Comercio A Pago")
        comercio_b = crear_comercio(f"com_b_{uid}", f"com_b_{uid}@test.com", "Comercio B Pago")
        cliente = crear_usuario(f"cli_{uid}", f"cli_{uid}@test.com", "Cliente Pago")

        self._login_usuario(comercio_a)
        emision = self.client.post(
            "/api/comercio/emitir-vuelto/",
            {"cliente_id": cliente.id, "monto_excedente": "4.00"},
            format="json",
        )
        self.assertEqual(emision.status_code, status.HTTP_200_OK)
        self.assertEqual(emision.data["saldo_cliente"], 4.0)

        cliente.refresh_from_db()
        self.assertEqual(float(cliente.saldo_comercial), 4.0)

        self._login_usuario(cliente)
        response = self.client.post(
            "/api/comercio/pagar/",
            {"comercio_id": comercio_b.id, "monto": "2.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertIn("saldo_restante", response.data)
        self.assertNotIn("csrf", str(response.data).lower())

    def test_vistas_red_comercial_declaran_csrf_exempt(self):
        from comunidad.views import (
            CsrfExemptSessionAuthentication,
            EmitirVueltoComercialView,
            PagarConSaldoView,
        )

        self.assertIn(CsrfExemptSessionAuthentication, EmitirVueltoComercialView.authentication_classes)
        self.assertIn(CsrfExemptSessionAuthentication, PagarConSaldoView.authentication_classes)

"""Pruebas HU5 — Red Comercial (ComercioService)."""

from decimal import Decimal

from django.test import TestCase, override_settings

from comunidad.models import Publicacion, SaldoComercial, UsuarioAutorizado
from comunidad.services import BusinessError, ComercioService, PublicacionService, RegistroUsuarioService, TruequeService
from comunidad.tests.helpers import (
    CATEGORIA_MANTENIMIENTO,
    TITULO_FONTANERIA_GENERAL,
    TITULO_INSTALACION_ELECTRICA,
    crear_comercio,
    crear_publicacion,
    crear_usuario,
)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class HU5TestCase(TestCase):
    """Base para pruebas HU5 sin depender de bcrypt en el entorno de test."""

    def setUp(self):
        self.servicio = ComercioService()


class ComercioServiceHU5Tests(HU5TestCase):
    def test_registro_comercio_aparece_en_catalogo(self):
        email = "panaderia@test.com"
        UsuarioAutorizado.objects.guardar_email(email, "COMERCIO")

        RegistroUsuarioService().registrar_usuario(
            {
                "email": email,
                "username": "panaderia",
                "password": "testpass123",
                "nombre_real": "Panaderia Central",
                "es_comercio": True,
            }
        )
        usuario_normal = crear_usuario("vecino", "vecino@test.com", "Vecino Normal")

        comercios = self.servicio.listar_comercios()
        ids = {comercio.id for comercio in comercios}
        nombres = {comercio.nombre_real for comercio in comercios}

        self.assertIn("Panaderia Central", nombres)
        self.assertNotIn(usuario_normal.id, ids)

    def test_solo_comercio_puede_emitir_vuelto(self):
        usuario_normal = crear_usuario("normal", "normal@test.com", "Usuario Normal")
        cliente = crear_usuario("cliente", "cliente@test.com", "Cliente")

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.emitir_vuelto(
                usuario_normal,
                {"cliente_id": cliente.id, "monto_excedente": "1.00"},
            )

        self.assertEqual(contexto.exception.status_code, 403)

    def test_emision_actualiza_saldos_bilaterales(self):
        comercio_a = crear_comercio("comercio_a", "comercio_a@test.com", "Comercio A", saldo=Decimal("0.00"))
        cliente = crear_usuario("cliente", "cliente_bil@test.com", "Cliente Bilateral", saldo_comercial=Decimal("0.00"))

        self.servicio.emitir_vuelto(
            comercio_a,
            {"cliente_id": cliente.id, "monto_excedente": "4.50"},
        )

        cliente.refresh_from_db()
        comercio_a.refresh_from_db()

        self.assertEqual(cliente.saldo_comercial, Decimal("4.50"))
        self.assertEqual(comercio_a.saldo_comercial, Decimal("-4.50"))

    def test_emision_no_modifica_horas_de_vida(self):
        comercio = crear_comercio("com_horas", "com_horas@test.com", "Comercio Horas", horas=0.0)
        cliente = crear_usuario("cli_horas", "cli_horas@test.com", "Cliente Horas", horas=2.0)

        self.servicio.emitir_vuelto(
            comercio,
            {"cliente_id": cliente.id, "monto_excedente": "2.00"},
        )

        cliente.refresh_from_db()
        comercio.refresh_from_db()

        self.assertEqual(cliente.horas_de_vida, 2.0)
        self.assertEqual(comercio.horas_de_vida, 0.0)

    def test_emision_crea_movimiento_emision(self):
        comercio = crear_comercio("com_mov", "com_mov@test.com", "Comercio Mov")
        cliente = crear_usuario("cli_mov", "cli_mov@test.com", "Cliente Mov")

        self.servicio.emitir_vuelto(
            comercio,
            {"cliente_id": cliente.id, "monto_excedente": "4.50"},
        )

        movimiento = SaldoComercial.objects.get()
        self.assertEqual(movimiento.tipo_movimiento, "EMISION")
        self.assertEqual(movimiento.monto_excedente, Decimal("4.50"))
        self.assertEqual(movimiento.comercio_id, comercio.id)
        self.assertEqual(movimiento.cliente_id, cliente.id)

    def test_emision_faltan_datos_400(self):
        comercio = crear_comercio("com_datos", "com_datos@test.com", "Comercio Datos")
        cliente = crear_usuario("cli_datos", "cli_datos@test.com", "Cliente Datos")

        with self.assertRaises(BusinessError) as contexto_sin_cliente:
            self.servicio.emitir_vuelto(comercio, {"monto_excedente": "1.00"})

        with self.assertRaises(BusinessError) as contexto_sin_monto:
            self.servicio.emitir_vuelto(comercio, {"cliente_id": cliente.id})

        self.assertEqual(contexto_sin_cliente.exception.status_code, 400)
        self.assertEqual(contexto_sin_monto.exception.status_code, 400)

    def test_pago_en_comercio_tercero(self):
        comercio_a = crear_comercio("com_a", "com_a@test.com", "Comercio A", saldo=Decimal("0.00"))
        comercio_b = crear_comercio("com_b", "com_b@test.com", "Comercio B", saldo=Decimal("0.00"))
        cliente = crear_usuario("cli_tercero", "cli_tercero@test.com", "Cliente Tercero", saldo_comercial=Decimal("0.00"))

        self.servicio.emitir_vuelto(
            comercio_a,
            {"cliente_id": cliente.id, "monto_excedente": "4.50"},
        )
        self.servicio.pagar_con_saldo(
            cliente,
            {"comercio_id": comercio_b.id, "monto": "3.00"},
        )

        cliente.refresh_from_db()
        comercio_a.refresh_from_db()
        comercio_b.refresh_from_db()

        self.assertEqual(cliente.saldo_comercial, Decimal("1.50"))
        self.assertEqual(comercio_b.saldo_comercial, Decimal("3.00"))
        self.assertEqual(comercio_a.saldo_comercial, Decimal("-4.50"))

    def test_pago_saldo_insuficiente(self):
        comercio_b = crear_comercio("com_insuf", "com_insuf@test.com", "Comercio Insuf")
        cliente = crear_usuario(
            "cli_insuf",
            "cli_insuf@test.com",
            "Cliente Insuf",
            saldo_comercial=Decimal("1.00"),
        )

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.pagar_con_saldo(
                cliente,
                {"comercio_id": comercio_b.id, "monto": "3.00"},
            )

        self.assertIn("insuficiente", str(contexto.exception).lower())
        self.assertEqual(contexto.exception.status_code, 400)

    def test_pago_destino_no_es_comercio(self):
        usuario_normal = crear_usuario("destino", "destino@test.com", "No Comercio")
        cliente = crear_usuario(
            "cli_destino",
            "cli_destino@test.com",
            "Cliente Destino",
            saldo_comercial=Decimal("5.00"),
        )

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.pagar_con_saldo(
                cliente,
                {"comercio_id": usuario_normal.id, "monto": "2.00"},
            )

        self.assertIn("comercio activo", str(contexto.exception).lower())
        self.assertEqual(contexto.exception.status_code, 400)

    def test_pago_no_modifica_horas_de_vida(self):
        comercio_a = crear_comercio("com_ph", "com_ph@test.com", "Comercio Pago Horas", horas=1.0)
        comercio_b = crear_comercio("com_pb", "com_pb@test.com", "Comercio B Pago Horas", horas=0.5)
        cliente = crear_usuario("cli_ph", "cli_ph@test.com", "Cliente Pago Horas", horas=2.0)

        self.servicio.emitir_vuelto(
            comercio_a,
            {"cliente_id": cliente.id, "monto_excedente": "4.00"},
        )
        self.servicio.pagar_con_saldo(
            cliente,
            {"comercio_id": comercio_b.id, "monto": "1.50"},
        )

        cliente.refresh_from_db()
        comercio_a.refresh_from_db()
        comercio_b.refresh_from_db()

        self.assertEqual(cliente.horas_de_vida, 2.0)
        self.assertEqual(comercio_a.horas_de_vida, 1.0)
        self.assertEqual(comercio_b.horas_de_vida, 0.5)

    def test_flujo_completo_interoperabilidad_A_a_B(self):
        comercio_a = crear_comercio("com_readme_a", "com_readme_a@test.com", "Comercio A README", saldo=Decimal("0.00"))
        comercio_b = crear_comercio("com_readme_b", "com_readme_b@test.com", "Comercio B README", saldo=Decimal("0.00"))
        cliente = crear_usuario(
            "cli_readme",
            "cli_readme@test.com",
            "Cliente README",
            horas=3.5,
            saldo_comercial=Decimal("0.00"),
        )

        self.servicio.emitir_vuelto(
            comercio_a,
            {"cliente_id": cliente.id, "monto_excedente": "4.50"},
        )
        self.servicio.pagar_con_saldo(
            cliente,
            {"comercio_id": comercio_b.id, "monto": "3.00"},
        )

        cliente.refresh_from_db()
        comercio_a.refresh_from_db()
        comercio_b.refresh_from_db()

        self.assertEqual(cliente.saldo_comercial, Decimal("1.50"))
        self.assertEqual(comercio_a.saldo_comercial, Decimal("-4.50"))
        self.assertEqual(comercio_b.saldo_comercial, Decimal("3.00"))
        self.assertEqual(cliente.horas_de_vida, 3.5)

    def test_pago_crea_movimiento_pago(self):
        comercio_a = crear_comercio("com_pa", "com_pa@test.com", "Comercio Emisor")
        comercio_b = crear_comercio("com_pb_mov", "com_pb_mov@test.com", "Comercio Receptor")
        cliente = crear_usuario("cli_pa", "cli_pa@test.com", "Cliente Pago Mov")

        self.servicio.emitir_vuelto(
            comercio_a,
            {"cliente_id": cliente.id, "monto_excedente": "5.00"},
        )
        self.servicio.pagar_con_saldo(
            cliente,
            {"comercio_id": comercio_b.id, "monto": "3.00"},
        )

        movimiento_pago = SaldoComercial.objects.filter(tipo_movimiento="PAGO").get()
        self.assertEqual(movimiento_pago.monto_excedente, Decimal("3.00"))
        self.assertEqual(movimiento_pago.comercio_id, comercio_b.id)
        self.assertEqual(movimiento_pago.cliente_id, cliente.id)


class RegistroComercioHU5Tests(HU5TestCase):
    def test_registro_comercio_sin_publicaciones_en_cartelera(self):
        email = "sin_pub@test.com"
        UsuarioAutorizado.objects.guardar_email(email, "COMERCIO")

        comercio = RegistroUsuarioService().registrar_usuario(
            {
                "email": email,
                "username": "sin_pub",
                "password": "testpass123",
                "nombre_real": "Comercio Sin Pub",
                "es_comercio": True,
            }
        )

        self.assertTrue(comercio.es_comercio)
        self.assertEqual(Publicacion.objects.filter(usuario=comercio).count(), 0)

        nombres = {item.nombre_real for item in self.servicio.listar_comercios()}
        self.assertIn("Comercio Sin Pub", nombres)

    def test_registro_comercio_rechaza_email_columna_usuarios(self):
        email = "solo_vecino@test.com"
        UsuarioAutorizado.objects.guardar_email(email, "USUARIO")

        with self.assertRaises(BusinessError) as contexto:
            RegistroUsuarioService().registrar_usuario(
                {
                    "email": email,
                    "username": "comercio_falso",
                    "password": "testpass123",
                    "nombre_real": "Comercio Falso",
                    "es_comercio": True,
                }
            )

        self.assertEqual(contexto.exception.status_code, 403)
        self.assertIn("Comercio no autorizado", str(contexto.exception))

    def test_registro_vecino_rechaza_email_columna_comercios(self):
        email = "solo_comercio@test.com"
        UsuarioAutorizado.objects.guardar_email(email, "COMERCIO")

        with self.assertRaises(BusinessError) as contexto:
            RegistroUsuarioService().registrar_usuario(
                {
                    "email": email,
                    "username": "vecino_falso",
                    "password": "testpass123",
                    "nombre_real": "Vecino Falso",
                    "es_comercio": False,
                }
            )

        self.assertEqual(contexto.exception.status_code, 403)
        self.assertIn("Usuario no autorizado", str(contexto.exception))

    def test_registro_comercio_habilita_emision_vuelto(self):
        email = "emision_directa@test.com"
        UsuarioAutorizado.objects.guardar_email(email, "COMERCIO")

        comercio = RegistroUsuarioService().registrar_usuario(
            {
                "email": email,
                "username": "emision_directa",
                "password": "testpass123",
                "nombre_real": "Comercio Emision",
                "es_comercio": True,
            }
        )
        cliente = crear_usuario("cli_emision", "cli_emision@test.com", "Cliente Emision")

        resultado = self.servicio.emitir_vuelto(
            comercio,
            {"cliente_id": cliente.id, "monto_excedente": "2.00"},
        )

        self.assertIn("comprobante", resultado)
        self.assertEqual(Publicacion.objects.filter(usuario=comercio).count(), 0)


class ListadoClientesHU5Tests(HU5TestCase):
    def test_listar_clientes_excluye_comercios(self):
        vecino_a = crear_usuario("vecino_a", "vecino_a@test.com", "Vecino A")
        vecino_b = crear_usuario("vecino_b", "vecino_b@test.com", "Vecino B")
        comercio = crear_comercio("com_local", "com_local@test.com", "Comercio Local")

        clientes = self.servicio.listar_clientes()
        ids = {cliente.id for cliente in clientes}

        self.assertIn(vecino_a.id, ids)
        self.assertIn(vecino_b.id, ids)
        self.assertNotIn(comercio.id, ids)

    def test_listar_clientes_solo_activos(self):
        vecino_activo = crear_usuario("vecino_act", "vecino_act@test.com", "Vecino Activo")
        vecino_inactivo = crear_usuario(
            "vecino_inact",
            "vecino_inact@test.com",
            "Vecino Inactivo",
            is_active=False,
        )

        clientes = self.servicio.listar_clientes()
        ids = {cliente.id for cliente in clientes}

        self.assertIn(vecino_activo.id, ids)
        self.assertNotIn(vecino_inactivo.id, ids)

    def test_emitir_vuelto_con_cliente_de_lista(self):
        comercio = crear_comercio("com_lista", "com_lista@test.com", "Comercio Lista")
        cliente_obj = crear_usuario("cli_lista", "cli_lista@test.com", "Cliente Lista")

        clientes = self.servicio.listar_clientes()
        ids = {cliente.id for cliente in clientes}
        self.assertIn(cliente_obj.id, ids)

        resultado = self.servicio.emitir_vuelto(
            comercio,
            {"cliente_id": cliente_obj.id, "monto_excedente": "3.50"},
        )

        self.assertIn("comprobante", resultado)
        cliente_obj.refresh_from_db()
        self.assertEqual(cliente_obj.saldo_comercial, Decimal("3.50"))


class RolComercioHU5Tests(HU5TestCase):
    def setUp(self):
        super().setUp()
        self.publicacion_service = PublicacionService()
        self.trueque_service = TruequeService()

    def test_comercio_no_puede_crear_publicacion(self):
        comercio = crear_comercio("com_pub", "com_pub@test.com", "Comercio Pub")

        with self.assertRaises(BusinessError) as contexto:
            self.publicacion_service.crear_publicacion(
                comercio,
                {
                    "tipo": "TALENTO",
                    "titulo": TITULO_INSTALACION_ELECTRICA,
                    "descripcion": "Servicio comercial",
                    "categoria": CATEGORIA_MANTENIMIENTO,
                },
            )

        self.assertEqual(contexto.exception.status_code, 403)
        self.assertIn("no pueden publicar", str(contexto.exception).lower())

    def test_vecino_si_puede_crear_publicacion(self):
        vecino = crear_usuario("vec_pub", "vec_pub@test.com", "Vecino Pub")

        publicacion = self.publicacion_service.crear_publicacion(
            vecino,
            {
                "tipo": "TALENTO",
                "titulo": TITULO_INSTALACION_ELECTRICA,
                "descripcion": "Ofrezco instalacion",
                "categoria": CATEGORIA_MANTENIMIENTO,
            },
        )

        self.assertEqual(publicacion.usuario_id, vecino.id)
        self.assertEqual(publicacion.tipo, "TALENTO")

    def test_comercio_no_puede_crear_propuesta_trueque(self):
        comercio = crear_comercio("com_prop", "com_prop@test.com", "Comercio Prop")
        receptor = crear_usuario("rec_prop", "rec_prop@test.com", "Receptor Prop")
        pub_emisor = crear_publicacion(
            receptor, "TALENTO", TITULO_INSTALACION_ELECTRICA, CATEGORIA_MANTENIMIENTO
        )
        pub_receptor = crear_publicacion(
            receptor, "NECESIDAD", TITULO_FONTANERIA_GENERAL, CATEGORIA_MANTENIMIENTO
        )

        with self.assertRaises(BusinessError) as contexto:
            self.trueque_service.crear_propuesta(
                comercio,
                receptor.id,
                pub_emisor.id,
                pub_receptor.id,
            )

        self.assertEqual(contexto.exception.status_code, 403)
        self.assertIn("no participan del mercado de trueques", str(contexto.exception).lower())

    def test_no_emitir_vuelto_a_otro_comercio(self):
        comercio_a = crear_comercio("com_a_v", "com_a_v@test.com", "Comercio A Vuelto")
        comercio_b = crear_comercio("com_b_v", "com_b_v@test.com", "Comercio B Vuelto")

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.emitir_vuelto(
                comercio_a,
                {"cliente_id": comercio_b.id, "monto_excedente": "2.00"},
            )

        self.assertEqual(contexto.exception.status_code, 400)
        self.assertIn("No se puede emitir vuelto a otro comercio", str(contexto.exception))

    def test_emision_con_valor_y_recibido_persiste_detalle(self):
        comercio = crear_comercio("com_det", "com_det@test.com", "Comercio Detalle")
        cliente = crear_usuario("cli_det", "cli_det@test.com", "Cliente Detalle")

        self.servicio.emitir_vuelto(
            comercio,
            {
                "cliente_id": cliente.id,
                "valor_producto": "5.00",
                "monto_recibido": "10.00",
                "monto_excedente": "5.00",
            },
        )

        movimiento = SaldoComercial.objects.get()
        self.assertEqual(movimiento.valor_producto, Decimal("5.00"))
        self.assertEqual(movimiento.monto_recibido, Decimal("10.00"))
        self.assertEqual(movimiento.monto_excedente, Decimal("5.00"))

    def test_emision_rechaza_excedente_inconsistente(self):
        comercio = crear_comercio("com_inc", "com_inc@test.com", "Comercio Inconsistente")
        cliente = crear_usuario("cli_inc", "cli_inc@test.com", "Cliente Inconsistente")

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.emitir_vuelto(
                comercio,
                {
                    "cliente_id": cliente.id,
                    "valor_producto": "5.00",
                    "monto_recibido": "10.00",
                    "monto_excedente": "4.00",
                },
            )

        self.assertEqual(contexto.exception.status_code, 400)
        self.assertIn("no coincide", str(contexto.exception).lower())

    def test_emision_rechaza_recibido_menor_o_igual_que_valor(self):
        comercio = crear_comercio("com_rec", "com_rec@test.com", "Comercio Recibido")
        cliente = crear_usuario("cli_rec", "cli_rec@test.com", "Cliente Recibido")

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.emitir_vuelto(
                comercio,
                {
                    "cliente_id": cliente.id,
                    "valor_producto": "10.00",
                    "monto_recibido": "7.00",
                },
            )

        self.assertEqual(contexto.exception.status_code, 400)
        self.assertIn("debe ser mayor", str(contexto.exception).lower())

    def test_emision_rechaza_excedente_cero(self):
        comercio = crear_comercio("com_cero", "com_cero@test.com", "Comercio Cero")
        cliente = crear_usuario("cli_cero", "cli_cero@test.com", "Cliente Cero")

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.emitir_vuelto(
                comercio,
                {
                    "cliente_id": cliente.id,
                    "valor_producto": "10.00",
                    "monto_recibido": "10.00",
                },
            )

        self.assertEqual(contexto.exception.status_code, 400)
        self.assertIn("debe ser mayor", str(contexto.exception).lower())

    def test_comercio_no_puede_pagar_con_saldo(self):
        comercio_a = crear_comercio("com_pago", "com_pago@test.com", "Comercio Pago", saldo=Decimal("5.00"))
        comercio_b = crear_comercio("com_dest", "com_dest@test.com", "Comercio Destino")

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.pagar_con_saldo(
                comercio_a,
                {"comercio_id": comercio_b.id, "monto": "2.00"},
            )

        self.assertEqual(contexto.exception.status_code, 400)
        self.assertIn("no pueden pagar", str(contexto.exception).lower())

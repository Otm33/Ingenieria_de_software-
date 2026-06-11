"""Pruebas HU4 — Emparejamiento y Gestión de Acuerdos."""

from django.db import IntegrityError
from django.db.models import Q
from django.test import TestCase, override_settings

from comunidad.models import AcuerdoTrueque, NotificacionPropuesta, Publicacion, Resena, Usuario
from comunidad.repositories import MatchmakingRepository
from comunidad.serializers import NotificacionSerializer
from comunidad.services import BusinessError, MatchmakingService, ResenaService, TruequeService
from comunidad.tests.helpers import (
    CATEGORIA_MANTENIMIENTO,
    TITULO_FONTANERIA_GENERAL,
    TITULO_INSTALACION_ELECTRICA,
    crear_publicacion,
    crear_resena,
    crear_trueque,
    crear_usuario,
)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class HU4TestCase(TestCase):
    """Base para pruebas HU4 sin depender de bcrypt en el entorno de test."""


class PreparacionHU4Tests(HU4TestCase):
    """Fase 0: verifica que los helpers de prueba funcionan correctamente."""

    def test_helpers_crean_usuario_y_publicaciones_del_catalogo(self):
        usuario_a = crear_usuario("vecino_a", "a@test.com", "Vecino A", horas=2.0)
        usuario_b = crear_usuario("vecino_b", "b@test.com", "Vecino B", horas=-1.0)

        pub_talento_a = crear_publicacion(
            usuario_a,
            tipo="TALENTO",
            titulo=TITULO_INSTALACION_ELECTRICA,
            categoria=CATEGORIA_MANTENIMIENTO,
        )
        pub_necesidad_a = crear_publicacion(
            usuario_a,
            tipo="NECESIDAD",
            titulo=TITULO_FONTANERIA_GENERAL,
            categoria=CATEGORIA_MANTENIMIENTO,
        )
        pub_talento_b = crear_publicacion(
            usuario_b,
            tipo="TALENTO",
            titulo=TITULO_FONTANERIA_GENERAL,
            categoria=CATEGORIA_MANTENIMIENTO,
        )
        pub_necesidad_b = crear_publicacion(
            usuario_b,
            tipo="NECESIDAD",
            titulo=TITULO_INSTALACION_ELECTRICA,
            categoria=CATEGORIA_MANTENIMIENTO,
        )

        self.assertEqual(usuario_a.horas_de_vida, 2.0)
        self.assertEqual(usuario_b.horas_de_vida, -1.0)
        self.assertTrue(pub_talento_a.esta_activa)
        self.assertEqual(pub_necesidad_b.titulo, TITULO_INSTALACION_ELECTRICA)


class ModelosHU4Tests(HU4TestCase):
    """Fase 1: modelos, migraciones y restricciones de reseñas."""

    def test_promedio_estrellas_sin_resenas_retorna_5(self):
        usuario = crear_usuario("sin_resenas", "sin@test.com", "Sin Resenas")
        self.assertEqual(usuario.promedio_estrellas, 5.0)

    def test_promedio_estrellas_calculado_desde_resenas(self):
        calificado = crear_usuario("calificado", "calificado@test.com", "Calificado")
        calificador_a = crear_usuario("calificador_a", "ca@test.com", "Calificador A")
        calificador_b = crear_usuario("calificador_b", "cb@test.com", "Calificador B")

        trueque_a = crear_trueque(calificador_a, calificado)
        trueque_b = crear_trueque(calificador_b, calificado)
        crear_resena(trueque_a, calificador_a, calificado, estrellas=3)
        crear_resena(trueque_b, calificador_b, calificado, estrellas=5)

        self.assertEqual(calificado.promedio_estrellas, 4.0)

    def test_dos_resenas_mismo_trueque_usuarios_distintos_ok(self):
        emisor = crear_usuario("emisor", "emisor@test.com", "Emisor")
        receptor = crear_usuario("receptor", "receptor@test.com", "Receptor")
        trueque = crear_trueque(emisor, receptor)

        resena_emisor = crear_resena(trueque, emisor, receptor, estrellas=4, comentario="Buen servicio.")
        resena_receptor = crear_resena(trueque, receptor, emisor, estrellas=5, comentario="Muy puntual.")

        self.assertEqual(trueque.resenas.count(), 2)
        self.assertNotEqual(resena_emisor.id, resena_receptor.id)

    def test_duplicar_resena_mismo_calificador_trueque_falla(self):
        emisor = crear_usuario("dup_emisor", "dpe@test.com", "Dup Emisor")
        receptor = crear_usuario("dup_receptor", "dpr@test.com", "Dup Receptor")
        trueque = crear_trueque(emisor, receptor)
        crear_resena(trueque, emisor, receptor, estrellas=4)

        with self.assertRaises(IntegrityError):
            Resena.objects.create(
                trueque=trueque,
                calificador=emisor,
                calificado=receptor,
                estrellas=2,
                comentario="Intento duplicado.",
            )


class ServiciosHU4Tests(HU4TestCase):
    """Fase 2: repositorios y servicios del backend core."""

    def setUp(self):
        self.matchmaking_repo = MatchmakingRepository()
        self.matchmaking_service = MatchmakingService(
            matchmaking_repository=self.matchmaking_repo
        )
        self.trueque_service = TruequeService()

    def _crear_par_complementario(self):
        user_a = crear_usuario("user_a", "ua@test.com", "User A")
        user_b = crear_usuario("user_b", "ub@test.com", "User B")
        crear_publicacion(
            user_a, "TALENTO", TITULO_INSTALACION_ELECTRICA, CATEGORIA_MANTENIMIENTO
        )
        crear_publicacion(
            user_a, "NECESIDAD", TITULO_FONTANERIA_GENERAL, CATEGORIA_MANTENIMIENTO
        )
        crear_publicacion(
            user_b, "TALENTO", TITULO_FONTANERIA_GENERAL, CATEGORIA_MANTENIMIENTO
        )
        crear_publicacion(
            user_b, "NECESIDAD", TITULO_INSTALACION_ELECTRICA, CATEGORIA_MANTENIMIENTO
        )
        return user_a, user_b

    def test_match_por_titulo_complementario(self):
        user_a, user_b = self._crear_par_complementario()
        matches = self.matchmaking_repo.buscar_matches(
            user_a,
            [TITULO_FONTANERIA_GENERAL],
            [TITULO_INSTALACION_ELECTRICA],
        )
        ids = [match["usuario"].id for match in matches]
        self.assertIn(user_b.id, ids)

    def test_match_no_coincide_si_solo_un_lado(self):
        user_a, _ = self._crear_par_complementario()
        user_c = crear_usuario("user_c", "uc@test.com", "User C")
        crear_publicacion(
            user_c, "TALENTO", TITULO_FONTANERIA_GENERAL, CATEGORIA_MANTENIMIENTO
        )

        matches = self.matchmaking_repo.buscar_matches(
            user_a,
            [TITULO_FONTANERIA_GENERAL],
            [TITULO_INSTALACION_ELECTRICA],
        )
        ids = [match["usuario"].id for match in matches]
        self.assertNotIn(user_c.id, ids)

    def test_detectar_match_no_recrea_tras_descartar(self):
        user_a, user_b = self._crear_par_complementario()

        self.matchmaking_service.detectar_y_notificar_matches(user_a)
        notif = NotificacionPropuesta.objects.filter(
            tipo="MATCH",
            destinatario=user_a,
        ).first()
        self.assertIsNotNone(notif)

        from comunidad.repositories import NotificacionPropuestaRepository

        NotificacionPropuestaRepository().marcar_como_leida(notif.id, destinatario=user_a)

        count_antes = NotificacionPropuesta.objects.filter(tipo="MATCH").count()
        self.matchmaking_service.detectar_y_notificar_matches(user_a)
        count_despues = NotificacionPropuesta.objects.filter(tipo="MATCH").count()

        self.assertEqual(count_antes, count_despues)

    def test_match_complementario_guarda_ambos_talentos(self):
        user_a, user_b = self._crear_par_complementario()

        self.matchmaking_service.detectar_y_notificar_matches(user_a)

        trueque = AcuerdoTrueque.objects.filter(
            Q(emisor=user_a, receptor=user_b) | Q(emisor=user_b, receptor=user_a),
            estado="PENDIENTE",
        ).first()
        self.assertIsNotNone(trueque)
        self.assertEqual(trueque.publicacion_emisor.tipo, "TALENTO")
        self.assertEqual(trueque.publicacion_receptor.tipo, "TALENTO")
        self.assertTrue(self.trueque_service._es_intercambio_mutuo(trueque))

    def test_match_notificacion_incluye_dos_parejas(self):
        user_a, user_b = self._crear_par_complementario()

        self.matchmaking_service.detectar_y_notificar_matches(user_a)

        notif = NotificacionPropuesta.objects.get(
            tipo="MATCH",
            destinatario=user_a,
            remitente=user_b,
        )
        self.assertIsNotNone(notif.match_detalle)
        self.assertEqual(len(notif.match_detalle), 2)

        recibo = next(entrada for entrada in notif.match_detalle if entrada["rol"] == "recibo")
        doy = next(entrada for entrada in notif.match_detalle if entrada["rol"] == "doy")

        self.assertEqual(recibo["mi_titulo"], TITULO_FONTANERIA_GENERAL)
        self.assertEqual(recibo["mi_tipo"], "NECESIDAD")
        self.assertEqual(recibo["su_titulo"], TITULO_FONTANERIA_GENERAL)
        self.assertEqual(recibo["su_tipo"], "TALENTO")
        self.assertEqual(doy["mi_titulo"], TITULO_INSTALACION_ELECTRICA)
        self.assertEqual(doy["mi_tipo"], "TALENTO")
        self.assertEqual(doy["su_titulo"], TITULO_INSTALACION_ELECTRICA)
        self.assertEqual(doy["su_tipo"], "NECESIDAD")

        data = NotificacionSerializer(notif).data
        self.assertEqual(len(data["match_detalle"]), 2)
        self.assertIn(TITULO_FONTANERIA_GENERAL, notif.mensaje)
        self.assertIn(TITULO_INSTALACION_ELECTRICA, notif.mensaje)

    def test_match_notifica_a_ambos_usuarios(self):
        user_a, user_b = self._crear_par_complementario()

        self.matchmaking_service.detectar_y_notificar_matches(user_a)

        notificaciones = NotificacionPropuesta.objects.filter(tipo="MATCH")
        self.assertEqual(notificaciones.count(), 2)
        self.assertTrue(
            notificaciones.filter(destinatario=user_a, remitente=user_b).exists()
        )
        self.assertTrue(
            notificaciones.filter(destinatario=user_b, remitente=user_a).exists()
        )

    def test_crear_propuesta_reutiliza_trueque_pendiente_del_match(self):
        user_a, user_b = self._crear_par_complementario()

        self.matchmaking_service.detectar_y_notificar_matches(user_a)

        pendientes = AcuerdoTrueque.objects.filter(
            estado="PENDIENTE",
        ).filter(
            Q(emisor=user_a, receptor=user_b) | Q(emisor=user_b, receptor=user_a),
        )
        self.assertEqual(pendientes.count(), 1)
        trueque_match_id = pendientes.first().id

        pub_emisor = Publicacion.objects.get(usuario=user_a, tipo="TALENTO")
        pub_receptor = Publicacion.objects.get(
            usuario=user_b, tipo="NECESIDAD", titulo=TITULO_INSTALACION_ELECTRICA
        )

        trueque_propuesta = self.trueque_service.crear_propuesta(
            user_a,
            user_b.id,
            pub_emisor.id,
            pub_receptor.id,
        )

        pendientes_despues = AcuerdoTrueque.objects.filter(
            estado="PENDIENTE",
        ).filter(
            Q(emisor=user_a, receptor=user_b) | Q(emisor=user_b, receptor=user_a),
        )
        self.assertEqual(pendientes_despues.count(), 1)
        self.assertEqual(trueque_propuesta.id, trueque_match_id)
        self.assertEqual(trueque_propuesta.emisor, user_a)
        self.assertEqual(trueque_propuesta.receptor, user_b)
        self.assertEqual(trueque_propuesta.publicacion_emisor, pub_emisor)
        self.assertEqual(trueque_propuesta.publicacion_receptor, pub_receptor)

    def test_crear_propuesta_crea_notificacion_propuesta(self):
        emisor = crear_usuario("prop_emisor", "pe@test.com", "Prop Emisor")
        receptor = crear_usuario("prop_receptor", "pr@test.com", "Prop Receptor")
        pub_emisor = crear_publicacion(
            emisor, "TALENTO", TITULO_INSTALACION_ELECTRICA, CATEGORIA_MANTENIMIENTO
        )
        pub_receptor = crear_publicacion(
            receptor, "NECESIDAD", TITULO_FONTANERIA_GENERAL, CATEGORIA_MANTENIMIENTO
        )

        trueque = self.trueque_service.crear_propuesta(
            emisor,
            receptor.id,
            pub_emisor.id,
            pub_receptor.id,
        )

        notificacion = NotificacionPropuesta.objects.get(trueque=trueque)
        self.assertEqual(notificacion.tipo, "PROPUESTA")
        self.assertEqual(notificacion.destinatario, receptor)
        self.assertEqual(notificacion.publicacion_original, pub_receptor)
        self.assertIn("ofrece", notificacion.mensaje)
        self.assertIn("necesidad", notificacion.mensaje)

    def test_crear_propuesta_necesidad_necesidad_falla(self):
        emisor = crear_usuario("nec_emisor", "ne@test.com", "Nec Emisor")
        receptor = crear_usuario("nec_receptor", "nr@test.com", "Nec Receptor")
        pub_emisor = crear_publicacion(
            emisor, "NECESIDAD", TITULO_FONTANERIA_GENERAL, CATEGORIA_MANTENIMIENTO
        )
        pub_receptor = crear_publicacion(
            receptor, "NECESIDAD", TITULO_INSTALACION_ELECTRICA, CATEGORIA_MANTENIMIENTO
        )

        with self.assertRaises(BusinessError) as contexto:
            self.trueque_service.crear_propuesta(
                emisor,
                receptor.id,
                pub_emisor.id,
                pub_receptor.id,
            )

        self.assertIn("dos necesidades", str(contexto.exception.message).lower())

    def test_crear_propuesta_talento_necesidad_ok(self):
        emisor = crear_usuario("tn_emisor", "tn@test.com", "TN Emisor")
        receptor = crear_usuario("tn_receptor", "tr@test.com", "TN Receptor")
        pub_emisor = crear_publicacion(
            emisor, "TALENTO", TITULO_INSTALACION_ELECTRICA, CATEGORIA_MANTENIMIENTO
        )
        pub_receptor = crear_publicacion(
            receptor, "NECESIDAD", TITULO_FONTANERIA_GENERAL, CATEGORIA_MANTENIMIENTO
        )

        trueque = self.trueque_service.crear_propuesta(
            emisor,
            receptor.id,
            pub_emisor.id,
            pub_receptor.id,
        )

        notificacion = NotificacionPropuesta.objects.get(trueque=trueque)
        self.assertEqual(notificacion.tipo, "PROPUESTA")
        self.assertEqual(notificacion.destinatario, receptor)

    def test_crear_propuesta_necesidad_talento_ok(self):
        emisor = crear_usuario("nt_emisor", "nte@test.com", "NT Emisor")
        receptor = crear_usuario("nt_receptor", "ntr@test.com", "NT Receptor")
        pub_emisor = crear_publicacion(
            emisor, "NECESIDAD", TITULO_FONTANERIA_GENERAL, CATEGORIA_MANTENIMIENTO
        )
        pub_receptor = crear_publicacion(
            receptor, "TALENTO", TITULO_INSTALACION_ELECTRICA, CATEGORIA_MANTENIMIENTO
        )

        trueque = self.trueque_service.crear_propuesta(
            emisor,
            receptor.id,
            pub_emisor.id,
            pub_receptor.id,
        )

        self.assertEqual(trueque.publicacion_emisor, pub_emisor)
        self.assertEqual(trueque.publicacion_receptor, pub_receptor)
        self.assertTrue(NotificacionPropuesta.objects.filter(trueque=trueque, tipo="PROPUESTA").exists())

    def test_crear_propuesta_talento_talento_ok_para_match(self):
        user_a, user_b = self._crear_par_complementario()
        pub_talento_a = Publicacion.objects.get(
            usuario=user_a, tipo="TALENTO", titulo=TITULO_INSTALACION_ELECTRICA
        )
        pub_talento_b = Publicacion.objects.get(
            usuario=user_b, tipo="TALENTO", titulo=TITULO_FONTANERIA_GENERAL
        )

        trueque = self.trueque_service.crear_propuesta(
            user_a,
            user_b.id,
            pub_talento_a.id,
            pub_talento_b.id,
        )

        self.assertEqual(trueque.publicacion_emisor.tipo, "TALENTO")
        self.assertEqual(trueque.publicacion_receptor.tipo, "TALENTO")
        self.assertTrue(self.trueque_service._es_intercambio_mutuo(trueque))

    def test_mensaje_propuesta_talento_necesidad(self):
        emisor = crear_usuario("msg_tn_emisor", "mte@test.com", "Mensaje TN Emisor")
        receptor = crear_usuario("msg_tn_receptor", "mtr@test.com", "Mensaje TN Receptor")
        pub_emisor = crear_publicacion(
            emisor, "TALENTO", TITULO_INSTALACION_ELECTRICA, CATEGORIA_MANTENIMIENTO
        )
        pub_receptor = crear_publicacion(
            receptor, "NECESIDAD", TITULO_FONTANERIA_GENERAL, CATEGORIA_MANTENIMIENTO
        )

        trueque = self.trueque_service.crear_propuesta(
            emisor,
            receptor.id,
            pub_emisor.id,
            pub_receptor.id,
        )
        notificacion = NotificacionPropuesta.objects.get(trueque=trueque)

        self.assertIn("ofrece", notificacion.mensaje)
        self.assertIn(TITULO_INSTALACION_ELECTRICA, notificacion.mensaje)
        self.assertIn("necesidad", notificacion.mensaje.lower())
        self.assertIn(TITULO_FONTANERIA_GENERAL, notificacion.mensaje)

    def test_mensaje_propuesta_necesidad_talento(self):
        emisor = crear_usuario("msg_nt_emisor", "mne@test.com", "Mensaje NT Emisor")
        receptor = crear_usuario("msg_nt_receptor", "mnr@test.com", "Mensaje NT Receptor")
        pub_emisor = crear_publicacion(
            emisor, "NECESIDAD", TITULO_FONTANERIA_GENERAL, CATEGORIA_MANTENIMIENTO
        )
        pub_receptor = crear_publicacion(
            receptor, "TALENTO", TITULO_INSTALACION_ELECTRICA, CATEGORIA_MANTENIMIENTO
        )

        trueque = self.trueque_service.crear_propuesta(
            emisor,
            receptor.id,
            pub_emisor.id,
            pub_receptor.id,
        )
        notificacion = NotificacionPropuesta.objects.get(trueque=trueque)

        self.assertIn("solicita", notificacion.mensaje)
        self.assertIn("talento", notificacion.mensaje.lower())
        self.assertIn(TITULO_INSTALACION_ELECTRICA, notificacion.mensaje)
        self.assertIn(TITULO_FONTANERIA_GENERAL, notificacion.mensaje)

    def test_responder_aceptar_estado_aceptado(self):
        emisor = crear_usuario("acep_emisor", "ae@test.com", "Acep Emisor")
        receptor = crear_usuario("acep_receptor", "ar@test.com", "Acep Receptor")
        pub_emisor = crear_publicacion(
            emisor, "TALENTO", TITULO_INSTALACION_ELECTRICA, CATEGORIA_MANTENIMIENTO
        )
        pub_receptor = crear_publicacion(
            receptor, "NECESIDAD", TITULO_FONTANERIA_GENERAL, CATEGORIA_MANTENIMIENTO
        )
        trueque = self.trueque_service.crear_propuesta(
            emisor, receptor.id, pub_emisor.id, pub_receptor.id
        )

        self.trueque_service.responder_propuesta(receptor, trueque.id, "ACEPTAR")
        trueque.refresh_from_db()
        self.assertEqual(trueque.estado, "ACEPTADO")

    def test_finalizar_una_confirmacion_no_mueve_saldo(self):
        prestador = crear_usuario("prestador", "prest@test.com", "Prestador", horas=0.0)
        receptor_servicio = crear_usuario(
            "rec_serv", "recs@test.com", "Recibe Servicio", horas=5.0
        )
        pub_prestador = crear_publicacion(
            prestador, "TALENTO", TITULO_INSTALACION_ELECTRICA, CATEGORIA_MANTENIMIENTO
        )
        pub_receptor = crear_publicacion(
            receptor_servicio, "NECESIDAD", TITULO_INSTALACION_ELECTRICA, CATEGORIA_MANTENIMIENTO
        )
        trueque = crear_trueque(
            prestador,
            receptor_servicio,
            estado="ACEPTADO",
            publicacion_emisor=pub_prestador,
            publicacion_receptor=pub_receptor,
        )

        resultado = self.trueque_service.finalizar_trueque(prestador, trueque.id)
        trueque.refresh_from_db()
        prestador.refresh_from_db()
        receptor_servicio.refresh_from_db()

        self.assertFalse(resultado["saldo_transferido"])
        self.assertTrue(trueque.emisor_confirmado)
        self.assertFalse(trueque.receptor_confirmado)
        self.assertEqual(trueque.estado, "ACEPTADO")
        self.assertEqual(prestador.horas_de_vida, 0.0)
        self.assertEqual(receptor_servicio.horas_de_vida, 5.0)

    def test_finalizar_match_mutuo_no_mueve_saldo(self):
        user_a, user_b = self._crear_par_complementario()
        pub_talento_a = Publicacion.objects.get(
            usuario=user_a, tipo="TALENTO", titulo=TITULO_INSTALACION_ELECTRICA
        )
        pub_talento_b = Publicacion.objects.get(
            usuario=user_b, tipo="TALENTO", titulo=TITULO_FONTANERIA_GENERAL
        )
        trueque = crear_trueque(
            user_a,
            user_b,
            estado="ACEPTADO",
            publicacion_emisor=pub_talento_a,
            publicacion_receptor=pub_talento_b,
        )

        horas_a_antes = user_a.horas_de_vida
        horas_b_antes = user_b.horas_de_vida

        self.trueque_service.finalizar_trueque(user_a, trueque.id)
        resultado = self.trueque_service.finalizar_trueque(user_b, trueque.id)

        user_a.refresh_from_db()
        user_b.refresh_from_db()
        trueque.refresh_from_db()

        self.assertTrue(self.trueque_service._es_intercambio_mutuo(trueque))
        self.assertFalse(resultado["saldo_transferido"])
        self.assertEqual(resultado["impacto_horas"], 0)
        self.assertTrue(resultado["habilitar_resena"])
        self.assertEqual(trueque.estado, "FINALIZADO")
        self.assertEqual(user_a.horas_de_vida, horas_a_antes)
        self.assertEqual(user_b.horas_de_vida, horas_b_antes)

    def test_finalizar_doble_confirmacion_mueve_saldo(self):
        prestador = crear_usuario("prest2", "prest2@test.com", "Prestador 2", horas=0.0)
        receptor_servicio = crear_usuario(
            "rec_serv2", "recs2@test.com", "Recibe Servicio 2", horas=5.0
        )
        pub_prestador = crear_publicacion(
            prestador, "TALENTO", TITULO_INSTALACION_ELECTRICA, CATEGORIA_MANTENIMIENTO
        )
        pub_receptor = crear_publicacion(
            receptor_servicio, "NECESIDAD", TITULO_INSTALACION_ELECTRICA, CATEGORIA_MANTENIMIENTO
        )
        trueque = crear_trueque(
            prestador,
            receptor_servicio,
            estado="ACEPTADO",
            publicacion_emisor=pub_prestador,
            publicacion_receptor=pub_receptor,
        )

        self.trueque_service.finalizar_trueque(prestador, trueque.id)
        resultado = self.trueque_service.finalizar_trueque(receptor_servicio, trueque.id)

        prestador.refresh_from_db()
        receptor_servicio.refresh_from_db()
        trueque.refresh_from_db()

        self.assertTrue(resultado["saldo_transferido"])
        self.assertTrue(resultado["habilitar_resena"])
        self.assertEqual(prestador.horas_de_vida, 1.0)
        self.assertEqual(receptor_servicio.horas_de_vida, 4.0)
        self.assertEqual(trueque.estado, "FINALIZADO")

    def test_finalizar_bloqueado_si_excede_limite_menos_10(self):
        prestador = crear_usuario("prest3", "prest3@test.com", "Prestador 3", horas=0.0)
        receptor_servicio = crear_usuario(
            "rec_serv3", "recs3@test.com", "Recibe Servicio 3", horas=-10.0
        )
        pub_prestador = crear_publicacion(
            prestador, "TALENTO", TITULO_INSTALACION_ELECTRICA, CATEGORIA_MANTENIMIENTO
        )
        pub_receptor = crear_publicacion(
            receptor_servicio, "NECESIDAD", TITULO_INSTALACION_ELECTRICA, CATEGORIA_MANTENIMIENTO
        )
        trueque = crear_trueque(
            prestador,
            receptor_servicio,
            estado="ACEPTADO",
            emisor_confirmado=True,
            publicacion_emisor=pub_prestador,
            publicacion_receptor=pub_receptor,
        )

        with self.assertRaises(BusinessError):
            self.trueque_service.finalizar_trueque(receptor_servicio, trueque.id)

    def test_registrar_resena_dos_usuarios_mismo_trueque(self):
        resena_service = ResenaService()
        emisor = crear_usuario("res_emisor", "re@test.com", "Res Emisor")
        receptor = crear_usuario("res_receptor", "rr@test.com", "Res Receptor")
        trueque = crear_trueque(emisor, receptor, estado="FINALIZADO")

        resena_service.registrar_resena(
            emisor, {"trueque_id": trueque.id, "estrellas": 4, "comentario": "Bien."}
        )
        resena_service.registrar_resena(
            receptor, {"trueque_id": trueque.id, "estrellas": 5, "comentario": "Excelente."}
        )

        self.assertEqual(trueque.resenas.count(), 2)

    def test_promedio_via_property_tras_resenas(self):
        resena_service = ResenaService()
        calificado = crear_usuario("calif_svc", "cs@test.com", "Calificado Svc")
        calificador_a = crear_usuario("calif_a", "ca2@test.com", "Calif A")
        calificador_b = crear_usuario("calif_b", "cb2@test.com", "Calif B")

        trueque_a = crear_trueque(calificador_a, calificado, estado="FINALIZADO")
        trueque_b = crear_trueque(calificador_b, calificado, estado="FINALIZADO")

        resena_service.registrar_resena(
            calificador_a, {"trueque_id": trueque_a.id, "estrellas": 3, "comentario": "Ok."}
        )
        resena_service.registrar_resena(
            calificador_b, {"trueque_id": trueque_b.id, "estrellas": 5, "comentario": "Genial."}
        )

        calificado.refresh_from_db()
        self.assertEqual(calificado.promedio_estrellas, 4.0)
        nombres_campos = {campo.name for campo in Usuario._meta.get_fields()}
        self.assertNotIn("promedio_estrellas", nombres_campos)

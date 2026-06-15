"""Pruebas Fase 2 Sprint 2 HU1 — ImpactoSocialService."""

from decimal import Decimal

from django.test import TestCase, override_settings

from comunidad.models import DonacionHoras, Publicacion, Usuario
from comunidad.services import (
    MENSAJE_COMERCIO_NO_IMPACTO_SOCIAL,
    MENSAJE_DONACION_EXITOSA,
    MENSAJE_MONTO_MINIMO_DONACION,
    MENSAJE_NECESIDAD_YA_VINCULADA,
    MENSAJE_NO_ACTIVAR_SOLICITUD_AJENA,
    MENSAJE_NO_DONAR_PROPIA_CAUSA,
    MENSAJE_RECEPTOR_MAS_10_HORAS,
    MENSAJE_SALDO_POSITIVO_DONACION,
    MENSAJE_SOLO_VULNERABLE_CRITICO,
    MENSAJE_SOLICITUD_NO_APROBADA_ACTIVAR,
    MENSAJE_TIEMPO_PRESTADO,
    MENSAJE_TOPE_HORAS_RECIBIDAS,
    MENSAJE_TITULO_CAUSA_INVALIDO,
    MENSAJE_CATEGORIA_TITULO_INCONSISTENTES,
    BusinessError,
    ImpactoSocialService,
    TruequeService,
)
from comunidad.tests.helpers import (
    CATEGORIA_CAUSA_SOCIAL_EJEMPLO,
    CATEGORIA_EDUCACION_CAUSA_SOCIAL,
    CATEGORIA_MANTENIMIENTO,
    CATEGORIA_TRANSPORTE_CAUSA_SOCIAL,
    TITULO_APOYO_ESCOLAR_PRIMARIA,
    TITULO_CAUSA_SOCIAL_EJEMPLO,
    TITULO_CONDUCTOR_REEMPLAZO,
    TITULO_INSTALACION_ELECTRICA,
    crear_publicacion,
    crear_trueque,
    crear_comercio,
    crear_usuario,
    datos_solicitud_social_validos,
    marcar_vulnerable,
)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class ImpactoSocialTestCase(TestCase):
    """Base para pruebas de ImpactoSocialService."""

    def setUp(self):
        self.servicio = ImpactoSocialService()
        self.admin = crear_usuario("admin_impacto", "admin_impacto@test.com", "Admin Impacto")
        self.admin.is_staff = True
        self.admin.save(update_fields=["is_staff"])
        self.fondo = Usuario.objects.get(username="fondo_comunitario")

    def _crear_solicitud_aprobada(self, solicitante=None, titulo=TITULO_CAUSA_SOCIAL_EJEMPLO):
        solicitante = solicitante or crear_usuario("solicitante", "sol@test.com", "Solicitante")
        solicitud = self.servicio.crear_solicitud(
            solicitante,
            datos_solicitud_social_validos(titulo=titulo),
        )
        self.servicio.aprobar_solicitud(self.admin, solicitud.id)
        solicitante.refresh_from_db()
        solicitud.refresh_from_db()
        return solicitante, solicitud


class GrupoASolicitudesTests(ImpactoSocialTestCase):
    """Grupo A — Solicitudes."""

    def test_usuario_crea_solicitud_queda_pendiente(self):
        usuario = crear_usuario("vecino_a", "vecino_a@test.com", "Vecino A")
        solicitud = self.servicio.crear_solicitud(
            usuario,
            datos_solicitud_social_validos(
                titulo=TITULO_APOYO_ESCOLAR_PRIMARIA,
                categoria=CATEGORIA_EDUCACION_CAUSA_SOCIAL,
                descripcion="Necesito apoyo para materiales.",
            ),
        )
        self.assertEqual(solicitud.estado, "PENDIENTE")
        usuario.refresh_from_db()
        self.assertEqual(usuario.estado_social, "NINGUNO")

    def test_usuario_normal_puede_crear_solicitud_pendiente(self):
        usuario = crear_usuario("normal_pub", "normal_pub@test.com", "Usuario Normal Pub")
        solicitud = self.servicio.crear_solicitud(
            usuario,
            datos_solicitud_social_validos(),
        )
        self.assertEqual(solicitud.estado, "PENDIENTE")
        usuario.refresh_from_db()
        self.assertEqual(usuario.estado_social, "NINGUNO")

    def test_solicitud_pendiente_no_en_listado_publico(self):
        usuario = crear_usuario("vecino_b", "vecino_b@test.com", "Vecino B")
        self.servicio.crear_solicitud(
            usuario,
            datos_solicitud_social_validos(
                titulo="Fisioterapia en casa",
                descripcion="Aún no aprobada.",
            ),
        )
        ids_publicas = {item["id"] for item in self.servicio.listar_solicitudes_aprobadas()}
        self.assertEqual(ids_publicas, set())

    def test_comercio_no_puede_crear_solicitud(self):
        comercio = crear_comercio("comercio_sol", "comercio_sol@test.com", "Comercio Sol")

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.crear_solicitud(
                comercio,
                datos_solicitud_social_validos(descripcion="No permitido."),
            )

        self.assertEqual(contexto.exception.status_code, 403)
        self.assertEqual(contexto.exception.message, MENSAJE_COMERCIO_NO_IMPACTO_SOCIAL)

    def test_admin_aprueba_solicitud(self):
        usuario = crear_usuario("vecino_c", "vecino_c@test.com", "Vecino C")
        solicitud = self.servicio.crear_solicitud(
            usuario,
            datos_solicitud_social_validos(
                titulo="Cuidado de pacientes",
                descripcion="Pendiente de revisión.",
            ),
        )
        aprobada = self.servicio.aprobar_solicitud(self.admin, solicitud.id)
        self.assertEqual(aprobada.estado, "APROBADA")
        self.assertEqual(aprobada.aprobada_por_id, self.admin.id)

    def test_solicitud_aprobada_visible_en_listado(self):
        usuario = crear_usuario("vecino_d", "vecino_d@test.com", "Vecino D")
        solicitud = self.servicio.crear_solicitud(
            usuario,
            datos_solicitud_social_validos(
                titulo=TITULO_CONDUCTOR_REEMPLAZO,
                categoria=CATEGORIA_TRANSPORTE_CAUSA_SOCIAL,
                descripcion="Debe aparecer en el listado.",
            ),
        )
        self.servicio.aprobar_solicitud(self.admin, solicitud.id)

        listado = self.servicio.listar_solicitudes_aprobadas()
        self.assertEqual(len(listado), 1)
        self.assertEqual(listado[0]["id"], solicitud.id)
        self.assertEqual(listado[0]["categoria"], CATEGORIA_TRANSPORTE_CAUSA_SOCIAL)
        self.assertEqual(listado[0]["estado_social_solicitante"], "VULNERABLE")

    def test_listar_solicitudes_aprobadas_incluye_datos_receptor(self):
        solicitante = crear_usuario(
            "sol_datos_receptor",
            "sol_datos_receptor@test.com",
            "Solicitante Datos",
            horas=5.0,
            horas_recibidas_donacion=3.0,
        )
        self._crear_solicitud_aprobada(solicitante=solicitante)

        listado = self.servicio.listar_solicitudes_aprobadas()
        self.assertEqual(len(listado), 1)
        self.assertEqual(listado[0]["horas_recibidas_donacion_solicitante"], 3.0)
        self.assertEqual(listado[0]["horas_de_vida_solicitante"], 5.0)


class GrupoBDonacionExitosaTests(ImpactoSocialTestCase):
    """Grupo B — Escenario 2 (donación exitosa)."""

    def test_donacion_exitosa_descuenta_y_acredita(self):
        donante = crear_usuario("donante_ok", "donante_ok@test.com", "Donante OK", horas=5.0)
        solicitante, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("receptor_ok", "receptor_ok@test.com", "Receptor OK"),
        )

        self.servicio.donar_a_causa(donante, solicitud.id, 2.0)

        donante.refresh_from_db()
        solicitante.refresh_from_db()
        solicitud.refresh_from_db()
        self.assertEqual(donante.horas_de_vida, 3.0)
        self.assertEqual(solicitud.horas_solidarias_disponibles, 2.0)
        self.assertEqual(solicitante.horas_de_vida, 0.0)

    def test_donacion_incrementa_horas_recibidas_donacion(self):
        donante = crear_usuario("donante_inc", "donante_inc@test.com", "Donante Inc", horas=4.0)
        solicitante, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("receptor_inc", "receptor_inc@test.com", "Receptor Inc"),
        )

        self.servicio.donar_a_causa(donante, solicitud.id, 1.5)

        solicitante.refresh_from_db()
        self.assertEqual(solicitante.horas_recibidas_donacion, 1.5)

    def test_donacion_incrementa_horas_recibidas_solicitud(self):
        donante = crear_usuario("donante_sol", "donante_sol@test.com", "Donante Sol", horas=4.0)
        solicitante, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("receptor_sol", "receptor_sol@test.com", "Receptor Sol"),
        )

        self.servicio.donar_a_causa(donante, solicitud.id, 2.0)

        solicitud.refresh_from_db()
        self.assertEqual(solicitud.horas_recibidas, 2.0)

    def test_donacion_crea_registro_ledger(self):
        donante = crear_usuario("donante_led", "donante_led@test.com", "Donante Led", horas=3.0)
        _, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("receptor_led", "receptor_led@test.com", "Receptor Led"),
        )

        resultado = self.servicio.donar_a_causa(donante, solicitud.id, 1.0)

        self.assertTrue(
            DonacionHoras.objects.filter(
                id=resultado["donacion_id"],
                tipo_destino="CAUSA",
                monto=1.0,
            ).exists(),
        )

    def test_donacion_retorna_mensaje_exitoso(self):
        donante = crear_usuario("donante_msg", "donante_msg@test.com", "Donante Msg", horas=3.0)
        _, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("receptor_msg", "receptor_msg@test.com", "Receptor Msg"),
        )

        resultado = self.servicio.donar_a_causa(donante, solicitud.id, 1.0)
        self.assertIn(MENSAJE_DONACION_EXITOSA, resultado["mensaje"])

    def test_donacion_es_irreversible(self):
        donante = crear_usuario("donante_irr", "donante_irr@test.com", "Donante Irr", horas=3.0)
        solicitante, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("receptor_irr", "receptor_irr@test.com", "Receptor Irr"),
        )

        self.servicio.donar_a_causa(donante, solicitud.id, 1.0)
        donante.refresh_from_db()
        solicitante.refresh_from_db()
        solicitud.refresh_from_db()

        self.assertFalse(hasattr(self.servicio, "revertir_donacion"))
        self.assertEqual(donante.horas_de_vida, 2.0)
        self.assertEqual(solicitud.horas_solidarias_disponibles, 1.0)
        self.assertEqual(solicitante.horas_de_vida, 0.0)

    def test_donacion_causa_no_incrementa_horas_de_vida_receptor(self):
        donante = crear_usuario("donante_no_hv", "donante_no_hv@test.com", "Donante No HV", horas=4.0)
        solicitante, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("receptor_no_hv", "receptor_no_hv@test.com", "Receptor No HV", horas=3.0),
        )

        self.servicio.donar_a_causa(donante, solicitud.id, 1.5)

        solicitante.refresh_from_db()
        self.assertEqual(solicitante.horas_de_vida, 3.0)
        self.assertEqual(solicitante.horas_recibidas_donacion, 1.5)

    def test_donacion_causa_incrementa_horas_solidarias_solicitud(self):
        donante = crear_usuario("donante_sol_causa", "donante_sol_causa@test.com", "Donante Sol Causa", horas=5.0)
        _, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("receptor_sol_causa", "receptor_sol_causa@test.com", "Receptor Sol Causa"),
        )

        self.servicio.donar_a_causa(donante, solicitud.id, 2.5)

        solicitud.refresh_from_db()
        self.assertEqual(solicitud.horas_solidarias_disponibles, 2.5)
        self.assertEqual(solicitud.horas_recibidas, 2.5)


class GrupoCSaldoInsuficienteTests(ImpactoSocialTestCase):
    """Grupo C — Escenario 3 (saldo insuficiente)."""

    def test_donacion_bloqueada_saldo_cero(self):
        donante = crear_usuario("donante_cero", "donante_cero@test.com", "Donante Cero", horas=0.0)
        _, solicitud = self._crear_solicitud_aprobada()

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.donar_a_causa(donante, solicitud.id, 1.0)

        self.assertEqual(contexto.exception.message, MENSAJE_SALDO_POSITIVO_DONACION)

    def test_donacion_bloqueada_saldo_negativo(self):
        donante = crear_usuario("donante_neg", "donante_neg@test.com", "Donante Neg", horas=-1.0)
        _, solicitud = self._crear_solicitud_aprobada()

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.donar_a_causa(donante, solicitud.id, 1.0)

        self.assertEqual(contexto.exception.message, MENSAJE_SALDO_POSITIVO_DONACION)

    def test_donacion_bloqueada_tiempo_prestado(self):
        donante = crear_usuario("donante_prest", "donante_prest@test.com", "Donante Prest", horas=2.0)
        _, solicitud = self._crear_solicitud_aprobada()

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.donar_a_causa(donante, solicitud.id, 3.0)

        self.assertEqual(contexto.exception.message, MENSAJE_TIEMPO_PRESTADO)


class GrupoDReglasAdicionalesTests(ImpactoSocialTestCase):
    """Grupo D — Reglas adicionales."""

    def test_donacion_minimo_05_horas(self):
        donante = crear_usuario("donante_min", "donante_min@test.com", "Donante Min", horas=2.0)
        _, solicitud = self._crear_solicitud_aprobada()

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.donar_a_causa(donante, solicitud.id, 0.3)

        self.assertEqual(contexto.exception.message, MENSAJE_MONTO_MINIMO_DONACION)

    def test_comercio_no_puede_donar(self):
        comercio = crear_comercio("comercio_don", "comercio_don@test.com", "Comercio Don", horas=5.0)
        _, solicitud = self._crear_solicitud_aprobada()

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.donar_a_causa(comercio, solicitud.id, 1.0)

        self.assertEqual(contexto.exception.status_code, 403)
        self.assertEqual(contexto.exception.message, MENSAJE_COMERCIO_NO_IMPACTO_SOCIAL)

    def test_no_puede_donar_a_propia_causa(self):
        solicitante = crear_usuario("donante_propia", "donante_propia@test.com", "Donante Propia", horas=5.0)
        _, solicitud = self._crear_solicitud_aprobada(solicitante=solicitante)

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.donar_a_causa(solicitante, solicitud.id, 1.0)

        self.assertEqual(contexto.exception.message, MENSAJE_NO_DONAR_PROPIA_CAUSA)
        solicitante.refresh_from_db()
        self.assertEqual(solicitante.horas_de_vida, 5.0)

    def test_receptor_mas_10_horas_no_recibe(self):
        donante = crear_usuario("donante_11", "donante_11@test.com", "Donante 11", horas=5.0)
        solicitante, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("receptor_11", "receptor_11@test.com", "Receptor 11", horas=11.0),
        )

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.donar_a_causa(donante, solicitud.id, 1.0)

        self.assertEqual(contexto.exception.message, MENSAJE_RECEPTOR_MAS_10_HORAS)
        solicitante.refresh_from_db()
        self.assertEqual(solicitante.horas_de_vida, 11.0)

    def test_tope_10_horas_recibidas_donacion(self):
        donante = crear_usuario("donante_tope", "donante_tope@test.com", "Donante Tope", horas=5.0)
        solicitante = crear_usuario(
            "receptor_tope",
            "receptor_tope@test.com",
            "Receptor Tope",
            horas=2.0,
            horas_recibidas_donacion=9.0,
        )
        _, solicitud = self._crear_solicitud_aprobada(solicitante=solicitante)

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.donar_a_causa(donante, solicitud.id, 2.0)

        self.assertEqual(contexto.exception.message, MENSAJE_TOPE_HORAS_RECIBIDAS)


class GrupoEFondoComunitarioTests(ImpactoSocialTestCase):
    """Grupo E — Escenario 4 (fondo comunitario)."""

    def test_donacion_a_fondo_acumula_saldo(self):
        donante = crear_usuario("donante_fondo", "donante_fondo@test.com", "Donante Fondo", horas=5.0)
        saldo_inicial = self.fondo.horas_de_vida

        self.servicio.donar_a_fondo(donante, 2.0)

        self.fondo.refresh_from_db()
        self.assertEqual(self.fondo.horas_de_vida, saldo_inicial + 2.0)

    def test_admin_asigna_fondo_a_vulnerable(self):
        vulnerable, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("vulnerable", "vulnerable@test.com", "Usuario Vulnerable"),
        )
        self.servicio.donar_a_fondo(
            crear_usuario("don_fondo_v", "don_fondo_v@test.com", "Don Fondo V", horas=5.0),
            3.0,
        )

        resultado = self.servicio.asignar_desde_fondo(self.admin, vulnerable.id, 2.0, solicitud.id)

        vulnerable.refresh_from_db()
        solicitud.refresh_from_db()
        self.assertEqual(vulnerable.horas_de_vida, 0.0)
        self.assertEqual(solicitud.horas_solidarias_disponibles, 2.0)
        self.assertEqual(resultado["monto"], 2.0)

    def test_admin_asigna_fondo_a_critico(self):
        critico = crear_usuario("critico", "critico@test.com", "Usuario Critico")
        solicitud = self.servicio.crear_solicitud(
            critico,
            datos_solicitud_social_validos(descripcion="Solicitud crítico."),
        )
        self.servicio.aprobar_solicitud(self.admin, solicitud.id)
        self.servicio.actualizar_estado_social(self.admin, critico.id, "CRITICO")
        self.servicio.donar_a_fondo(
            crear_usuario("don_fondo_c", "don_fondo_c@test.com", "Don Fondo C", horas=5.0),
            3.0,
        )

        self.servicio.asignar_desde_fondo(self.admin, critico.id, 1.5, solicitud.id)

        critico.refresh_from_db()
        solicitud.refresh_from_db()
        self.assertEqual(critico.horas_de_vida, 0.0)
        self.assertEqual(solicitud.horas_solidarias_disponibles, 1.5)
        self.assertEqual(critico.horas_recibidas_donacion, 1.5)

    def test_admin_no_asigna_fondo_a_usuario_normal(self):
        normal = crear_usuario("normal_fondo", "normal_fondo@test.com", "Usuario Normal")
        self.servicio.donar_a_fondo(
            crear_usuario("don_fondo_n", "don_fondo_n@test.com", "Don Fondo N", horas=5.0),
            3.0,
        )

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.asignar_desde_fondo(self.admin, normal.id, 1.0)

        self.assertEqual(contexto.exception.message, MENSAJE_SOLO_VULNERABLE_CRITICO)

    def test_asignacion_fondo_decrementa_saldo_fondo(self):
        vulnerable, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("vuln_saldo", "vuln_saldo@test.com", "Vulnerable Saldo"),
        )
        self.servicio.donar_a_fondo(
            crear_usuario("don_fondo_s", "don_fondo_s@test.com", "Don Fondo S", horas=5.0),
            4.0,
        )
        self.fondo.refresh_from_db()
        saldo_antes = self.fondo.horas_de_vida

        self.servicio.asignar_desde_fondo(self.admin, vulnerable.id, 1.5, solicitud.id)

        self.fondo.refresh_from_db()
        self.assertEqual(self.fondo.horas_de_vida, saldo_antes - 1.5)

    def test_asignar_desde_fondo_crea_registro_ledger(self):
        vulnerable, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("vuln_ledger", "vuln_ledger@test.com", "Vulnerable Ledger"),
        )
        self.servicio.donar_a_fondo(
            crear_usuario("don_ledger", "don_ledger@test.com", "Don Ledger", horas=5.0),
            3.0,
        )

        self.servicio.asignar_desde_fondo(self.admin, vulnerable.id, 2.0, solicitud.id)

        self.assertTrue(
            DonacionHoras.objects.filter(
                donante=self.fondo,
                receptor=vulnerable,
                tipo_destino="ASIGNACION",
                monto=2.0,
                solicitud=solicitud,
            ).exists(),
        )

    def test_asignacion_fondo_acredita_solicitud_no_horas_de_vida(self):
        vulnerable, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("vuln_sol", "vuln_sol@test.com", "Vulnerable Sol", horas=4.0),
        )
        self.servicio.donar_a_fondo(
            crear_usuario("don_vuln_sol", "don_vuln_sol@test.com", "Don Vuln Sol", horas=5.0),
            3.0,
        )

        self.servicio.asignar_desde_fondo(self.admin, vulnerable.id, 2.0, solicitud.id)

        vulnerable.refresh_from_db()
        solicitud.refresh_from_db()
        self.assertEqual(vulnerable.horas_de_vida, 4.0)
        self.assertEqual(solicitud.horas_solidarias_disponibles, 2.0)
        self.assertEqual(solicitud.horas_recibidas, 2.0)


class GrupoEHistorialDonacionesTests(ImpactoSocialTestCase):
    """Grupo E.1 — Historial de donaciones."""

    def test_listar_mis_donaciones_realizadas(self):
        donante = crear_usuario("don_real", "don_real@test.com", "Don Real", horas=5.0)
        _, solicitud = self._crear_solicitud_aprobada()

        self.servicio.donar_a_causa(donante, solicitud.id, 2.0)

        realizadas = self.servicio.listar_mis_donaciones_realizadas(donante)
        self.assertEqual(len(realizadas), 1)
        self.assertEqual(realizadas[0].monto, 2.0)
        self.assertEqual(realizadas[0].tipo_destino, "CAUSA")

    def test_listar_mis_donaciones_recibidas(self):
        donante = crear_usuario("don_rec", "don_rec@test.com", "Don Rec", horas=5.0)
        solicitante, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("receptor_rec", "receptor_rec@test.com", "Receptor Rec"),
        )

        self.servicio.donar_a_causa(donante, solicitud.id, 2.0)

        recibidas = self.servicio.listar_mis_donaciones_recibidas(solicitante)
        self.assertEqual(len(recibidas), 1)
        self.assertEqual(recibidas[0].monto, 2.0)
        self.assertEqual(recibidas[0].tipo_destino, "CAUSA")


class GrupoFAdminVulnerablesTests(ImpactoSocialTestCase):
    """Grupo F — Escenario 1 (admin vulnerables)."""

    def test_admin_marca_usuario_vulnerable(self):
        usuario = crear_usuario("marca_vuln", "marca_vuln@test.com", "Marca Vuln")
        actualizado = self.servicio.actualizar_estado_social(self.admin, usuario.id, "VULNERABLE")
        self.assertEqual(actualizado.estado_social, "VULNERABLE")

    def test_admin_marca_usuario_critico(self):
        usuario = crear_usuario("marca_crit", "marca_crit@test.com", "Marca Crit")
        actualizado = self.servicio.actualizar_estado_social(self.admin, usuario.id, "CRITICO")
        self.assertEqual(actualizado.estado_social, "CRITICO")

    def test_usuario_normal_no_puede_marcar_vulnerable(self):
        usuario = crear_usuario("normal_admin", "normal_admin@test.com", "Normal Admin")
        objetivo = crear_usuario("objetivo", "objetivo@test.com", "Objetivo")

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.actualizar_estado_social(usuario, objetivo.id, "VULNERABLE")

        self.assertEqual(contexto.exception.status_code, 403)


class GrupoGAislamientoSprint1Tests(ImpactoSocialTestCase):
    """Grupo G — Aislamiento Sprint 1."""

    def test_donacion_no_modifica_saldo_comercial(self):
        donante = crear_usuario(
            "donante_com",
            "donante_com@test.com",
            "Donante Com",
            horas=5.0,
            saldo_comercial=Decimal("12.50"),
        )
        _, solicitud = self._crear_solicitud_aprobada()

        self.servicio.donar_a_causa(donante, solicitud.id, 2.0)

        donante.refresh_from_db()
        self.assertEqual(donante.saldo_comercial, Decimal("12.50"))

    def test_donacion_no_modifica_horas_de_otros_usuarios(self):
        donante = crear_usuario("donante_otros", "donante_otros@test.com", "Donante Otros", horas=5.0)
        tercero = crear_usuario("tercero", "tercero@test.com", "Tercero", horas=7.0)
        _, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("receptor_otros", "receptor_otros@test.com", "Receptor Otros"),
        )

        self.servicio.donar_a_causa(donante, solicitud.id, 2.0)

        tercero.refresh_from_db()
        self.assertEqual(tercero.horas_de_vida, 7.0)


class GrupoIFlujoPublicacionAprobacionTests(ImpactoSocialTestCase):
    """Grupo I — Publicar → aprobar → Usuario Vulnerable."""

    def test_aprobar_solicitud_marca_solicitante_vulnerable(self):
        usuario = crear_usuario("sol_vuln", "sol_vuln@test.com", "Solicitante Vuln")
        solicitud = self.servicio.crear_solicitud(
            usuario,
            datos_solicitud_social_validos(),
        )

        self.servicio.aprobar_solicitud(self.admin, solicitud.id)

        usuario.refresh_from_db()
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, "APROBADA")
        self.assertEqual(usuario.estado_social, "VULNERABLE")

    def test_aprobar_no_degrada_critico_a_vulnerable(self):
        usuario = crear_usuario("sol_crit", "sol_crit@test.com", "Solicitante Critico")
        self.servicio.actualizar_estado_social(self.admin, usuario.id, "CRITICO")
        usuario.refresh_from_db()
        solicitud = self.servicio.crear_solicitud(
            usuario,
            datos_solicitud_social_validos(
                titulo="Orientación familiar",
            ),
        )

        self.servicio.aprobar_solicitud(self.admin, solicitud.id)

        usuario.refresh_from_db()
        self.assertEqual(usuario.estado_social, "CRITICO")

    def test_aprobar_no_cambia_si_ya_vulnerable(self):
        usuario = marcar_vulnerable(crear_usuario("ya_vuln", "ya_vuln@test.com", "Ya Vulnerable"))
        solicitud = self.servicio.crear_solicitud(
            usuario,
            datos_solicitud_social_validos(
                titulo="Enfermería a domicilio",
            ),
        )

        self.servicio.aprobar_solicitud(self.admin, solicitud.id)

        usuario.refresh_from_db()
        self.assertEqual(usuario.estado_social, "VULNERABLE")

    def test_rechazar_solicitud_no_cambia_estado_social(self):
        usuario = crear_usuario("sol_rech", "sol_rech@test.com", "Solicitante Rech")
        solicitud = self.servicio.crear_solicitud(
            usuario,
            datos_solicitud_social_validos(),
        )

        self.servicio.rechazar_solicitud(self.admin, solicitud.id)

        usuario.refresh_from_db()
        self.assertEqual(usuario.estado_social, "NINGUNO")


class GrupoHCatalogoCausasSocialesTests(ImpactoSocialTestCase):
    """Grupo H — Catálogo de causas sociales."""

    def test_crear_solicitud_con_titulo_catalogo_ok(self):
        usuario = crear_usuario("vuln_cat", "vuln_cat@test.com", "Usuario Cat")
        solicitud = self.servicio.crear_solicitud(
            usuario,
            datos_solicitud_social_validos(
                categoria=CATEGORIA_CAUSA_SOCIAL_EJEMPLO,
                titulo=TITULO_CAUSA_SOCIAL_EJEMPLO,
                descripcion="Solicitud con catálogo válido.",
            ),
        )
        self.assertEqual(solicitud.estado, "PENDIENTE")
        self.assertEqual(solicitud.categoria, CATEGORIA_CAUSA_SOCIAL_EJEMPLO)
        self.assertEqual(solicitud.titulo, TITULO_CAUSA_SOCIAL_EJEMPLO)

    def test_crear_solicitud_titulo_libre_rechazado(self):
        usuario = crear_usuario("vuln_libre", "vuln_libre@test.com", "Usuario Libre")

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.crear_solicitud(
                usuario,
                datos_solicitud_social_validos(titulo="Pintar interiores"),
            )

        self.assertEqual(contexto.exception.message, MENSAJE_TITULO_CAUSA_INVALIDO)

    def test_crear_solicitud_categoria_titulo_inconsistentes_rechazado(self):
        usuario = crear_usuario("vuln_inc", "vuln_inc@test.com", "Usuario Inc")

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.crear_solicitud(
                usuario,
                datos_solicitud_social_validos(
                    categoria="Educación, Asesoría y Tutorías",
                    titulo=TITULO_CAUSA_SOCIAL_EJEMPLO,
                ),
            )

        self.assertEqual(contexto.exception.message, MENSAJE_CATEGORIA_TITULO_INCONSISTENTES)

    def test_whitelist_titulos_pertenecen_a_catalogo_cartelera(self):
        from comunidad.catalogo_causas_sociales import (
            TITULOS_CAUSA_SOCIAL,
            titulo_pertenece_a_catalogo_cartelera,
        )

        for categoria, titulos in TITULOS_CAUSA_SOCIAL.items():
            for titulo in titulos:
                self.assertTrue(
                    titulo_pertenece_a_catalogo_cartelera(categoria, titulo),
                    msg=f"{titulo!r} no está en cartelera ({categoria!r})",
                )

    def test_activar_necesidad_usa_categoria_cartelera(self):
        from comunidad.services import CATEGORIAS_PUBLICACION

        usuario, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("sol_cat_cart", "sol_cat_cart@test.com", "Sol Cat Cart"),
        )

        self.servicio.activar_necesidad_vinculada(usuario, solicitud.id)

        publicacion = Publicacion.objects.get(solicitud_apoyo_social=solicitud)
        self.assertIn(publicacion.categoria, CATEGORIAS_PUBLICACION)
        self.assertEqual(publicacion.categoria, CATEGORIA_CAUSA_SOCIAL_EJEMPLO)

    def test_comercio_sigue_sin_poder_crear_solicitud(self):
        comercio = crear_comercio("comercio_cat", "comercio_cat@test.com", "Comercio Cat")

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.crear_solicitud(
                comercio,
                datos_solicitud_social_validos(),
            )

        self.assertEqual(contexto.exception.status_code, 403)
        self.assertEqual(contexto.exception.message, MENSAJE_COMERCIO_NO_IMPACTO_SOCIAL)


class GrupoJActivarNecesidadTests(ImpactoSocialTestCase):
    """Grupo J — Publicar necesidad vinculada a solicitud aprobada."""

    def test_activar_necesidad_solo_solicitud_aprobada(self):
        usuario = crear_usuario("sol_pend_act", "sol_pend_act@test.com", "Sol Pend Act")
        solicitud = self.servicio.crear_solicitud(
            usuario,
            datos_solicitud_social_validos(descripcion="Pendiente activar."),
        )

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.activar_necesidad_vinculada(usuario, solicitud.id)

        self.assertEqual(contexto.exception.message, MENSAJE_SOLICITUD_NO_APROBADA_ACTIVAR)
        self.assertFalse(Publicacion.objects.filter(usuario=usuario, es_causa_social=True).exists())

    def test_activar_necesidad_crea_publicacion_es_causa_social(self):
        usuario, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("sol_act_ok", "sol_act_ok@test.com", "Sol Act OK"),
        )

        resultado = self.servicio.activar_necesidad_vinculada(usuario, solicitud.id)

        publicacion = Publicacion.objects.get(id=resultado.publicacion_id)
        self.assertTrue(publicacion.es_causa_social)
        self.assertEqual(publicacion.tipo, "NECESIDAD")
        self.assertEqual(publicacion.titulo, solicitud.titulo)
        self.assertEqual(publicacion.descripcion, solicitud.descripcion)
        self.assertEqual(publicacion.categoria, solicitud.categoria)
        self.assertEqual(publicacion.urgencia, "ALTA")
        self.assertTrue(publicacion.esta_activa)

    def test_no_activar_dos_veces_misma_solicitud(self):
        usuario, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("sol_dup", "sol_dup@test.com", "Sol Dup"),
        )

        self.servicio.activar_necesidad_vinculada(usuario, solicitud.id)

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.activar_necesidad_vinculada(usuario, solicitud.id)

        self.assertEqual(contexto.exception.message, MENSAJE_NECESIDAD_YA_VINCULADA)
        self.assertEqual(Publicacion.objects.filter(usuario=usuario, es_causa_social=True).count(), 1)

    def test_usuario_normal_no_activa_solicitud_ajena(self):
        _, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("sol_propia", "sol_propia@test.com", "Sol Propia"),
        )
        otro = crear_usuario("otro_act", "otro_act@test.com", "Otro Act")

        with self.assertRaises(BusinessError) as contexto:
            self.servicio.activar_necesidad_vinculada(otro, solicitud.id)

        self.assertEqual(contexto.exception.message, MENSAJE_NO_ACTIVAR_SOLICITUD_AJENA)


class GrupoITruequeHorasSolidariasTests(ImpactoSocialTestCase):
    """Grupo I — Trueque con publicación de causa social consume horas solidarias."""

    def setUp(self):
        super().setUp()
        self.trueque_service = TruequeService()

    def _setup_trueque_social(self, horas_solidarias=3.0):
        vulnerable, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("vuln_trueque", "vuln_trueque@test.com", "Vuln Trueque", horas=2.0),
        )
        if horas_solidarias > 0:
            donante = crear_usuario("don_trueque", "don_trueque@test.com", "Don Trueque", horas=5.0)
            self.servicio.donar_a_causa(donante, solicitud.id, horas_solidarias)
            solicitud.refresh_from_db()

        self.servicio.activar_necesidad_vinculada(vulnerable, solicitud.id)
        solicitud.refresh_from_db()
        pub_necesidad = solicitud.publicacion

        prestador = crear_usuario("prest_trueque", "prest_trueque@test.com", "Prest Trueque", horas=0.0)
        pub_talento = crear_publicacion(
            prestador,
            "TALENTO",
            solicitud.titulo,
            solicitud.categoria,
        )
        trueque = self.trueque_service.crear_propuesta(
            prestador,
            vulnerable.id,
            pub_talento.id,
            pub_necesidad.id,
        )
        self.trueque_service.responder_propuesta(vulnerable, trueque.id, "ACEPTAR")
        return vulnerable, solicitud, prestador, trueque

    def _crear_trueque_anti_bypass(self, titulo=TITULO_CAUSA_SOCIAL_EJEMPLO, horas_solidarias=0.0, horas_vida_vulnerable=5.0):
        """Cartelera normal (sin activar_necesidad) con título igual a causa aprobada."""
        vulnerable, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario(
                "vuln_anti_bypass",
                "vuln_anti_bypass@test.com",
                "Vuln Anti-Bypass",
                horas=horas_vida_vulnerable,
            ),
            titulo=titulo,
        )

        if horas_solidarias > 0:
            donante = crear_usuario("don_ab", "don_ab@test.com", "Don Anti-Bypass", horas=10.0)
            self.servicio.donar_a_causa(donante, solicitud.id, horas_solidarias)
            solicitud.refresh_from_db()

        pub_necesidad_cartelera = crear_publicacion(
            vulnerable,
            "NECESIDAD",
            titulo,
            CATEGORIA_MANTENIMIENTO,
        )
        self.assertFalse(pub_necesidad_cartelera.es_causa_social)

        prestador = crear_usuario("prest_ab", "prest_ab@test.com", "Prest Anti-Bypass", horas=0.0)
        pub_talento = crear_publicacion(
            prestador,
            "TALENTO",
            titulo,
            CATEGORIA_MANTENIMIENTO,
        )
        trueque = self.trueque_service.crear_propuesta(
            prestador,
            vulnerable.id,
            pub_talento.id,
            pub_necesidad_cartelera.id,
        )
        self.trueque_service.responder_propuesta(vulnerable, trueque.id, "ACEPTAR")
        return vulnerable, solicitud, prestador, trueque

    def test_trueque_social_descuenta_horas_solidarias_no_generales(self):
        vulnerable, solicitud, prestador, trueque = self._setup_trueque_social(horas_solidarias=3.0)
        horas_vida_inicial = vulnerable.horas_de_vida

        self.trueque_service.finalizar_trueque(prestador, trueque.id)
        resultado = self.trueque_service.finalizar_trueque(vulnerable, trueque.id)

        vulnerable.refresh_from_db()
        solicitud.refresh_from_db()
        prestador.refresh_from_db()
        trueque.refresh_from_db()

        self.assertTrue(resultado["saldo_transferido"])
        self.assertEqual(trueque.estado, "FINALIZADO")
        self.assertEqual(vulnerable.horas_de_vida, horas_vida_inicial)
        self.assertEqual(solicitud.horas_solidarias_disponibles, 2.0)
        self.assertEqual(solicitud.horas_solidarias_utilizadas, 1.0)
        self.assertEqual(prestador.horas_de_vida, 1.0)

    def test_trueque_social_sin_saldo_solidario_falla(self):
        vulnerable, solicitud, prestador, trueque = self._setup_trueque_social(horas_solidarias=0.0)

        self.trueque_service.finalizar_trueque(prestador, trueque.id)

        with self.assertRaises(BusinessError) as contexto:
            self.trueque_service.finalizar_trueque(vulnerable, trueque.id)

        self.assertIn("horas solidarias suficientes", contexto.exception.message.lower())
        vulnerable.refresh_from_db()
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.horas_solidarias_disponibles, 0.0)
        self.assertEqual(vulnerable.horas_de_vida, 2.0)

    def test_trueque_causa_aprobada_mismo_titulo_obliga_solidarias(self):
        """Anti-bypass: NECESIDAD cartelera (es_causa_social=False) con título de causa aprobada."""
        vulnerable, solicitud, prestador, trueque = self._crear_trueque_anti_bypass(
            titulo=TITULO_CAUSA_SOCIAL_EJEMPLO,
            horas_solidarias=3.0,
        )
        horas_vida_inicial = vulnerable.horas_de_vida
        solidarias_inicial = solicitud.horas_solidarias_disponibles
        utilizadas_inicial = solicitud.horas_solidarias_utilizadas

        self.trueque_service.finalizar_trueque(prestador, trueque.id)
        self.trueque_service.finalizar_trueque(vulnerable, trueque.id)

        vulnerable.refresh_from_db()
        solicitud.refresh_from_db()
        prestador.refresh_from_db()

        self.assertEqual(vulnerable.horas_de_vida, horas_vida_inicial)
        self.assertEqual(solicitud.horas_solidarias_disponibles, solidarias_inicial - 1.0)
        self.assertEqual(solicitud.horas_solidarias_utilizadas, utilizadas_inicial + 1.0)
        self.assertEqual(prestador.horas_de_vida, 1.0)

    def test_trueque_causa_aprobada_sin_solidarias_falla(self):
        vulnerable, solicitud, prestador, trueque = self._crear_trueque_anti_bypass(
            titulo=TITULO_CAUSA_SOCIAL_EJEMPLO,
            horas_solidarias=0.0,
        )
        horas_vida_inicial = vulnerable.horas_de_vida

        self.trueque_service.finalizar_trueque(prestador, trueque.id)

        with self.assertRaises(BusinessError) as contexto:
            self.trueque_service.finalizar_trueque(vulnerable, trueque.id)

        self.assertIn("horas solidarias suficientes", contexto.exception.message.lower())
        vulnerable.refresh_from_db()
        solicitud.refresh_from_db()
        self.assertEqual(vulnerable.horas_de_vida, horas_vida_inicial)
        self.assertEqual(solicitud.horas_solidarias_disponibles, 0.0)

    def test_trueque_normal_sigue_usando_horas_de_vida(self):
        prestador = crear_usuario("prest_hu4", "prest_hu4@test.com", "Prest HU4", horas=0.0)
        receptor_servicio = crear_usuario(
            "rec_hu4",
            "rec_hu4@test.com",
            "Rec HU4",
            horas=5.0,
        )
        pub_prestador = crear_publicacion(
            prestador,
            "TALENTO",
            TITULO_INSTALACION_ELECTRICA,
            CATEGORIA_MANTENIMIENTO,
        )
        pub_receptor = crear_publicacion(
            receptor_servicio,
            "NECESIDAD",
            TITULO_INSTALACION_ELECTRICA,
            CATEGORIA_MANTENIMIENTO,
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

        self.assertTrue(resultado["saldo_transferido"])
        self.assertEqual(prestador.horas_de_vida, 1.0)
        self.assertEqual(receptor_servicio.horas_de_vida, 4.0)

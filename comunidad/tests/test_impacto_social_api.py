"""Pruebas API Fase 3 Sprint 2 HU1 — Impacto Social."""

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from comunidad.models import Usuario
from comunidad.services import (
    MENSAJE_COMERCIO_NO_IMPACTO_SOCIAL,
    MENSAJE_DONACION_EXITOSA,
    MENSAJE_NO_DONAR_PROPIA_CAUSA,
    MENSAJE_SALDO_POSITIVO_DONACION,
    MENSAJE_SIN_PERMISOS_ADMIN,
    MENSAJE_SOLO_VULNERABLE_CRITICO,
    MENSAJE_SOLICITANTE_MARCADO_VULNERABLE,
    MENSAJE_SOLICITUD_NO_APROBADA_ACTIVAR,
    MENSAJE_TITULO_CAUSA_INVALIDO,
    ImpactoSocialService,
)
from comunidad.tests.helpers import (
    CATEGORIA_CAUSA_SOCIAL_EJEMPLO,
    CATEGORIA_EDUCACION_CAUSA_SOCIAL,
    TITULO_APOYO_ESCOLAR_PRIMARIA,
    TITULO_CAUSA_SOCIAL_EJEMPLO,
    crear_comercio,
    crear_usuario,
    datos_solicitud_social_validos,
)


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class ImpactoSocialAPITestCase(APITestCase):
    """Base para pruebas API de Impacto Social."""

    def setUp(self):
        self.client = APIClient()
        self.servicio = ImpactoSocialService()
        self.admin = crear_usuario("admin_api", "admin_api@test.com", "Admin API")
        self.admin.is_staff = True
        self.admin.save(update_fields=["is_staff"])
        self.fondo = Usuario.objects.get(username="fondo_comunitario")

    def _crear_solicitud_aprobada(self, solicitante=None):
        solicitante = solicitante or crear_usuario(
            "sol_api",
            "sol_api@test.com",
            "Solicitante API",
        )
        solicitud = self.servicio.crear_solicitud(
            solicitante,
            datos_solicitud_social_validos(descripcion="Solicitud para pruebas API."),
        )
        self.servicio.aprobar_solicitud(self.admin, solicitud.id)
        solicitante.refresh_from_db()
        solicitud.refresh_from_db()
        return solicitante, solicitud


class APIImpactoSocialTests(ImpactoSocialAPITestCase):
    def test_get_solicitudes_sin_auth_401(self):
        response = self.client.get("/api/impacto-social/solicitudes/")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_post_solicitud_201(self):
        usuario = crear_usuario("post_sol", "post_sol@test.com", "Post Sol")
        self.client.force_authenticate(user=usuario)

        response = self.client.post(
            "/api/impacto-social/solicitudes/",
            datos_solicitud_social_validos(
                titulo="Cuidado de pacientes",
                descripcion="Descripción de la causa.",
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["estado"], "PENDIENTE")
        self.assertEqual(response.data["titulo"], "Cuidado de pacientes")
        self.assertEqual(response.data["categoria"], CATEGORIA_CAUSA_SOCIAL_EJEMPLO)

    def test_post_solicitud_con_catalogo_201(self):
        usuario = crear_usuario("post_cat", "post_cat@test.com", "Post Cat")
        self.client.force_authenticate(user=usuario)

        response = self.client.post(
            "/api/impacto-social/solicitudes/",
            datos_solicitud_social_validos(
                categoria=CATEGORIA_CAUSA_SOCIAL_EJEMPLO,
                titulo=TITULO_CAUSA_SOCIAL_EJEMPLO,
                descripcion="Solicitud con catálogo válido.",
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["categoria"], CATEGORIA_CAUSA_SOCIAL_EJEMPLO)
        self.assertEqual(response.data["titulo"], TITULO_CAUSA_SOCIAL_EJEMPLO)

    def test_post_solicitud_titulo_invalido_400(self):
        usuario = crear_usuario("post_inv", "post_inv@test.com", "Post Inv")
        self.client.force_authenticate(user=usuario)

        response = self.client.post(
            "/api/impacto-social/solicitudes/",
            datos_solicitud_social_validos(titulo="Pintar interiores"),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], MENSAJE_TITULO_CAUSA_INVALIDO)

    def test_post_solicitud_usuario_normal_201(self):
        usuario = crear_usuario("post_no_vuln", "post_no_vuln@test.com", "Post No Vuln")
        self.client.force_authenticate(user=usuario)

        response = self.client.post(
            "/api/impacto-social/solicitudes/",
            datos_solicitud_social_validos(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["estado"], "PENDIENTE")
        usuario.refresh_from_db()
        self.assertEqual(usuario.estado_social, "NINGUNO")

    def test_admin_aprobar_marca_solicitante_vulnerable(self):
        solicitante = crear_usuario("sol_apr_vuln", "sol_apr_vuln@test.com", "Sol Apr Vuln")
        solicitud = self.servicio.crear_solicitud(
            solicitante,
            datos_solicitud_social_validos(descripcion="Pendiente admin vulnerable."),
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/admin/impacto-social/solicitudes/{solicitud.id}/aprobar/",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], "APROBADA")
        self.assertEqual(response.data["mensaje"], MENSAJE_SOLICITANTE_MARCADO_VULNERABLE)
        solicitante.refresh_from_db()
        self.assertEqual(solicitante.estado_social, "VULNERABLE")

    def test_get_solicitudes_solo_aprobadas(self):
        usuario_pendiente = crear_usuario("pend_api", "pend_api@test.com", "Pendiente API")
        usuario_aprobada = crear_usuario("apr_api", "apr_api@test.com", "Aprobada API")
        self.servicio.crear_solicitud(
            usuario_pendiente,
            datos_solicitud_social_validos(
                titulo="Fisioterapia en casa",
                descripcion="No debe listarse.",
            ),
        )
        self._crear_solicitud_aprobada(solicitante=usuario_aprobada)

        consultante = crear_usuario("consulta", "consulta@test.com", "Consulta")
        self.client.force_authenticate(user=consultante)
        response = self.client.get("/api/impacto-social/solicitudes/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["cantidad"], 1)
        self.assertEqual(response.data["solicitudes"][0]["titulo"], TITULO_CAUSA_SOCIAL_EJEMPLO)
        self.assertEqual(response.data["solicitudes"][0]["categoria"], CATEGORIA_CAUSA_SOCIAL_EJEMPLO)

    def test_listar_solicitudes_aprobadas_incluye_datos_receptor(self):
        solicitante = crear_usuario(
            "sol_receptor",
            "sol_receptor@test.com",
            "Solicitante Receptor",
            horas=5.0,
            horas_recibidas_donacion=3.0,
        )
        self._crear_solicitud_aprobada(solicitante=solicitante)

        consultante = crear_usuario("consulta_receptor", "consulta_receptor@test.com", "Consulta Receptor")
        self.client.force_authenticate(user=consultante)
        response = self.client.get("/api/impacto-social/solicitudes/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["cantidad"], 1)
        solicitud = response.data["solicitudes"][0]
        self.assertEqual(solicitud["horas_recibidas_donacion_solicitante"], 3.0)
        self.assertEqual(solicitud["horas_de_vida_solicitante"], 5.0)

    def test_post_donar_200_comprobante(self):
        donante = crear_usuario("don_api", "don_api@test.com", "Donante API", horas=5.0)
        _, solicitud = self._crear_solicitud_aprobada()

        self.client.force_authenticate(user=donante)
        response = self.client.post(
            "/api/impacto-social/donar/",
            {"solicitud_id": solicitud.id, "monto": 2.0},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(MENSAJE_DONACION_EXITOSA, response.data["message"])
        self.assertIn("comprobante", response.data)
        self.assertEqual(response.data["comprobante"]["monto"], 2.0)
        self.assertEqual(response.data["comprobante"]["tipo_destino"], "CAUSA")
        self.assertIsNotNone(response.data["comprobante"]["comprobante_id"])

    def test_post_donar_saldo_cero_400(self):
        donante = crear_usuario("don_cero", "don_cero@test.com", "Donante Cero", horas=0.0)
        _, solicitud = self._crear_solicitud_aprobada()

        self.client.force_authenticate(user=donante)
        response = self.client.post(
            "/api/impacto-social/donar/",
            {"solicitud_id": solicitud.id, "monto": 1.0},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], MENSAJE_SALDO_POSITIVO_DONACION)

    def test_post_donar_propia_causa_400(self):
        solicitante = crear_usuario("don_propia_api", "don_propia_api@test.com", "Don Propia API", horas=5.0)
        _, solicitud = self._crear_solicitud_aprobada(solicitante=solicitante)

        self.client.force_authenticate(user=solicitante)
        response = self.client.post(
            "/api/impacto-social/donar/",
            {"solicitud_id": solicitud.id, "monto": 1.0},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], MENSAJE_NO_DONAR_PROPIA_CAUSA)
        solicitante.refresh_from_db()
        self.assertEqual(solicitante.horas_de_vida, 5.0)

    def test_post_donar_fondo_200(self):
        donante = crear_usuario("don_fondo_api", "don_fondo_api@test.com", "Don Fondo API", horas=5.0)
        saldo_inicial = self.fondo.horas_de_vida

        self.client.force_authenticate(user=donante)
        response = self.client.post(
            "/api/impacto-social/donar-fondo/",
            {"monto": 2.0},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("comprobante", response.data)
        self.assertEqual(response.data["comprobante"]["tipo_destino"], "FONDO")
        self.fondo.refresh_from_db()
        self.assertEqual(self.fondo.horas_de_vida, saldo_inicial + 2.0)
        self.assertEqual(response.data["saldo_fondo"], self.fondo.horas_de_vida)

    def test_comercio_post_donar_403(self):
        comercio = crear_comercio("com_don_api", "com_don_api@test.com", "Comercio Don API", horas=5.0)
        _, solicitud = self._crear_solicitud_aprobada()

        self.client.force_authenticate(user=comercio)
        response = self.client.post(
            "/api/impacto-social/donar/",
            {"solicitud_id": solicitud.id, "monto": 1.0},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], MENSAJE_COMERCIO_NO_IMPACTO_SOCIAL)

    def test_admin_aprobar_solicitud_200(self):
        solicitante = crear_usuario("sol_apr", "sol_apr@test.com", "Sol Apr")
        solicitud = self.servicio.crear_solicitud(
            solicitante,
            datos_solicitud_social_validos(
                titulo="Acompañamiento médico",
                categoria=CATEGORIA_CAUSA_SOCIAL_EJEMPLO,
                descripcion="Pendiente admin.",
            ),
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            f"/api/admin/impacto-social/solicitudes/{solicitud.id}/aprobar/",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], "APROBADA")

    def test_no_admin_aprobar_403(self):
        solicitante = crear_usuario("sol_no_admin", "sol_no_admin@test.com", "Sol No Admin")
        usuario = crear_usuario("no_admin", "no_admin@test.com", "No Admin")
        solicitud = self.servicio.crear_solicitud(
            solicitante,
            datos_solicitud_social_validos(
                titulo="Terapia de duelo",
                categoria=CATEGORIA_CAUSA_SOCIAL_EJEMPLO,
                descripcion="Sin permisos.",
            ),
        )

        self.client.force_authenticate(user=usuario)
        response = self.client.post(
            f"/api/admin/impacto-social/solicitudes/{solicitud.id}/aprobar/",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], MENSAJE_SIN_PERMISOS_ADMIN)

    def test_admin_patch_estado_social_200(self):
        objetivo = crear_usuario("obj_patch", "obj_patch@test.com", "Obj Patch")

        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            f"/api/admin/impacto-social/usuarios/{objetivo.id}/estado-social/",
            {"estado_social": "VULNERABLE"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado_social"], "VULNERABLE")

    def test_no_admin_patch_estado_social_403(self):
        objetivo = crear_usuario("obj_no_patch", "obj_no_patch@test.com", "Obj No Patch")
        usuario = crear_usuario("usr_no_patch", "usr_no_patch@test.com", "Usr No Patch")

        self.client.force_authenticate(user=usuario)
        response = self.client.patch(
            f"/api/admin/impacto-social/usuarios/{objetivo.id}/estado-social/",
            {"estado_social": "VULNERABLE"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], MENSAJE_SIN_PERMISOS_ADMIN)

    def test_admin_asignar_fondo_200(self):
        vulnerable, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("vuln_api", "vuln_api@test.com", "Vulnerable API"),
        )
        self.servicio.donar_a_fondo(
            crear_usuario("don_asig", "don_asig@test.com", "Don Asig", horas=5.0),
            3.0,
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/admin/impacto-social/fondo/asignar/",
            {"usuario_id": vulnerable.id, "solicitud_id": solicitud.id, "monto": 2.0},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["monto"], 2.0)
        self.assertEqual(response.data["solicitud_id"], solicitud.id)
        vulnerable.refresh_from_db()
        solicitud.refresh_from_db()
        self.assertEqual(vulnerable.horas_de_vida, 0.0)
        self.assertEqual(solicitud.horas_solidarias_disponibles, 2.0)

    def test_admin_asignar_fondo_no_vulnerable_400(self):
        normal = crear_usuario("normal_api", "normal_api@test.com", "Normal API")
        self.servicio.donar_a_fondo(
            crear_usuario("don_no_vuln", "don_no_vuln@test.com", "Don No Vuln", horas=5.0),
            3.0,
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/admin/impacto-social/fondo/asignar/",
            {"usuario_id": normal.id, "monto": 1.0},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], MENSAJE_SOLO_VULNERABLE_CRITICO)

    def test_get_mis_donaciones_200(self):
        donante = crear_usuario("don_hist_api", "don_hist_api@test.com", "Don Hist API", horas=5.0)
        _, solicitud = self._crear_solicitud_aprobada()

        self.client.force_authenticate(user=donante)
        donacion = self.client.post(
            "/api/impacto-social/donar/",
            {"solicitud_id": solicitud.id, "monto": 2.0},
            format="json",
        )
        self.assertEqual(donacion.status_code, status.HTTP_200_OK)

        response = self.client.get("/api/impacto-social/mis-donaciones/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["cantidad_realizadas"], 1)
        self.assertGreaterEqual(len(response.data["realizadas"]), 1)
        self.assertIn("comprobante_id", response.data["realizadas"][0])

    def test_get_mis_donaciones_sin_auth_401(self):
        response = self.client.get("/api/impacto-social/mis-donaciones/")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_post_activar_necesidad_200(self):
        usuario, solicitud = self._crear_solicitud_aprobada(
            solicitante=crear_usuario("act_api_ok", "act_api_ok@test.com", "Act API OK"),
        )

        self.client.force_authenticate(user=usuario)
        response = self.client.post(
            f"/api/impacto-social/solicitudes/{solicitud.id}/activar-necesidad/",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["publicacion_id"], response.data["solicitud"]["publicacion_id"])
        self.assertTrue(response.data["solicitud"]["necesidad_activa"])
        self.assertIsNotNone(response.data["publicacion_id"])

    def test_post_activar_necesidad_pendiente_400(self):
        usuario = crear_usuario("act_api_pend", "act_api_pend@test.com", "Act API Pend")
        solicitud = self.servicio.crear_solicitud(
            usuario,
            datos_solicitud_social_validos(descripcion="Pendiente API."),
        )

        self.client.force_authenticate(user=usuario)
        response = self.client.post(
            f"/api/impacto-social/solicitudes/{solicitud.id}/activar-necesidad/",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], MENSAJE_SOLICITUD_NO_APROBADA_ACTIVAR)


class CSRFImpactoSocialTests(ImpactoSocialAPITestCase):
    def _login_usuario(self, usuario, password="testpass123"):
        usuario.set_password(password)
        usuario.save()
        self.client = APIClient(enforce_csrf_checks=True)
        logged = self.client.login(username=usuario.username, password=password)
        self.assertTrue(logged)

    def test_post_solicitud_sin_csrf_token_ok(self):
        usuario = crear_usuario("pub_sol", "pub_sol@test.com", "Pub Sol")

        self._login_usuario(usuario)
        response = self.client.post(
            "/api/impacto-social/solicitudes/",
            datos_solicitud_social_validos(
                titulo=TITULO_APOYO_ESCOLAR_PRIMARIA,
                categoria=CATEGORIA_EDUCACION_CAUSA_SOCIAL,
                descripcion="Publicación con sesión sin token.",
            ),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["estado"], "PENDIENTE")
        self.assertEqual(response.data["categoria"], CATEGORIA_EDUCACION_CAUSA_SOCIAL)
        self.assertNotIn("csrf", str(response.data).lower())

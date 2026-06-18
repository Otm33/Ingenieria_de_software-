"""
Sprint 2 HU1: Tests de Impacto Social — Donaciones solidarias y gestión de apoyo social.
Adaptados a la arquitectura N-Tier de TuTrueque (Luigi).
"""
from django.test import TestCase

from backend.comunidad.models import (
    Usuario,
    SolicitudApoyoSocial,
    DonacionHoras,
)
from backend.comunidad.services import ImpactoSocialService
from backend.comunidad.services.base import BusinessError


def crear_usuario(username, horas=10.0, es_comercio=False, is_staff=False, is_superuser=False,
                  estado_social="NINGUNO", es_fondo_comunitario=False):
    u = Usuario.objects.create_user(
        username=username,
        email=f"{username}@test.com",
        password="testpass123",
        nombre_real=username.replace("_", " ").title(),
        horas_de_vida=horas,
        es_comercio=es_comercio,
        is_staff=is_staff,
        is_superuser=is_superuser,
        estado_social=estado_social,
        es_fondo_comunitario=es_fondo_comunitario,
    )
    return u


def crear_solicitud(solicitante, estado="PENDIENTE",
                    categoria="Cuidado de la Salud, Bienestar y Terapias",
                    titulo="Cuidado de abuelos",
                    descripcion="Necesito ayuda con mi abuelo"):
    return SolicitudApoyoSocial.objects.create(
        solicitante=solicitante,
        categoria=categoria,
        titulo=titulo,
        descripcion=descripcion,
        estado=estado,
    )


# ── Catálogo de Causas Sociales ───────────────────────────────────────────────

class TestCatalogoCausasSociales(TestCase):

    def test_titulo_permitido(self):
        from backend.comunidad.catalogo_causas_sociales import es_titulo_causa_social_permitido
        self.assertTrue(es_titulo_causa_social_permitido("Cuidado de abuelos"))

    def test_titulo_no_permitido(self):
        from backend.comunidad.catalogo_causas_sociales import es_titulo_causa_social_permitido
        self.assertFalse(es_titulo_causa_social_permitido("Limpieza profunda"))

    def test_categoria_permitida(self):
        from backend.comunidad.catalogo_causas_sociales import es_categoria_causa_social_permitida
        self.assertTrue(es_categoria_causa_social_permitida("Educación, Asesoría y Tutorías"))

    def test_categoria_no_permitida(self):
        from backend.comunidad.catalogo_causas_sociales import es_categoria_causa_social_permitida
        self.assertFalse(es_categoria_causa_social_permitida("Tecnología, Desarrollo y Redes"))

    def test_categoria_para_titulo(self):
        from backend.comunidad.catalogo_causas_sociales import categoria_para_titulo
        cat = categoria_para_titulo("Apoyo escolar primaria")
        self.assertEqual(cat, "Educación, Asesoría y Tutorías")

    def test_categoria_para_titulo_inexistente(self):
        from backend.comunidad.catalogo_causas_sociales import categoria_para_titulo
        cat = categoria_para_titulo("Servicio inventado")
        self.assertIsNone(cat)


# ── Servicio: Crear Solicitud ─────────────────────────────────────────────────

class TestCrearSolicitud(TestCase):

    def setUp(self):
        self.servicio = ImpactoSocialService()
        self.usuario = crear_usuario("solicitante", horas=5.0)

    def test_crear_solicitud_exitosa(self):
        datos = {
            "categoria": "Cuidado de la Salud, Bienestar y Terapias",
            "titulo": "Cuidado de abuelos",
            "descripcion": "Ayuda con mi abuelo enfermo",
        }
        solicitud = self.servicio.crear_solicitud(self.usuario, datos)
        self.assertEqual(solicitud.estado, "PENDIENTE")
        self.assertEqual(solicitud.solicitante, self.usuario)
        self.assertEqual(solicitud.titulo, "Cuidado de abuelos")

    def test_comercio_no_puede_solicitar(self):
        comercio = crear_usuario("comercio1", es_comercio=True)
        datos = {
            "categoria": "Cuidado de la Salud, Bienestar y Terapias",
            "titulo": "Cuidado de abuelos",
            "descripcion": "X",
        }
        with self.assertRaises(BusinessError):
            self.servicio.crear_solicitud(comercio, datos)

    def test_categoria_invalida_rechazada(self):
        datos = {
            "categoria": "Tecnología, Desarrollo y Redes",
            "titulo": "Cuidado de abuelos",
            "descripcion": "X",
        }
        with self.assertRaises(BusinessError):
            self.servicio.crear_solicitud(self.usuario, datos)

    def test_titulo_invalido_rechazado(self):
        datos = {
            "categoria": "Cuidado de la Salud, Bienestar y Terapias",
            "titulo": "Servicio no permitido",
            "descripcion": "X",
        }
        with self.assertRaises(BusinessError):
            self.servicio.crear_solicitud(self.usuario, datos)

    def test_titulo_categoria_inconsistentes(self):
        datos = {
            "categoria": "Automotriz, Transporte y Logística",
            "titulo": "Cuidado de abuelos",  # pertenece a Salud, no Automotriz
            "descripcion": "X",
        }
        with self.assertRaises(BusinessError):
            self.servicio.crear_solicitud(self.usuario, datos)

    def test_descripcion_vacia_rechazada(self):
        datos = {
            "categoria": "Cuidado de la Salud, Bienestar y Terapias",
            "titulo": "Cuidado de abuelos",
            "descripcion": "   ",
        }
        with self.assertRaises(BusinessError):
            self.servicio.crear_solicitud(self.usuario, datos)


# ── Servicio: Aprobar / Rechazar Solicitud ────────────────────────────────────

class TestAprobarRechazarSolicitud(TestCase):

    def setUp(self):
        self.servicio = ImpactoSocialService()
        self.admin = crear_usuario("admin_test", is_staff=True)
        self.usuario = crear_usuario("solicitante2", horas=3.0)
        self.solicitud = crear_solicitud(self.usuario)

    def test_admin_aprueba_solicitud(self):
        resultado = self.servicio.aprobar_solicitud(self.admin, self.solicitud.id)
        self.assertEqual(resultado.estado, "APROBADA")

    def test_aprobar_marca_vulnerable(self):
        resultado = self.servicio.aprobar_solicitud(self.admin, self.solicitud.id)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.estado_social, "VULNERABLE")
        self.assertTrue(getattr(resultado, "solicitante_marcado_vulnerable", False))

    def test_aprobar_sin_permisos_falla(self):
        usuario_normal = crear_usuario("normal_user")
        with self.assertRaises(BusinessError):
            self.servicio.aprobar_solicitud(usuario_normal, self.solicitud.id)

    def test_rechazar_solicitud(self):
        resultado = self.servicio.rechazar_solicitud(self.admin, self.solicitud.id)
        self.assertEqual(resultado.estado, "RECHAZADA")

    def test_no_aprobar_dos_veces(self):
        self.servicio.aprobar_solicitud(self.admin, self.solicitud.id)
        with self.assertRaises(BusinessError):
            self.servicio.aprobar_solicitud(self.admin, self.solicitud.id)

    def test_no_rechazar_aprobada(self):
        self.servicio.aprobar_solicitud(self.admin, self.solicitud.id)
        with self.assertRaises(BusinessError):
            self.servicio.rechazar_solicitud(self.admin, self.solicitud.id)


# ── Servicio: Donaciones ──────────────────────────────────────────────────────

class TestDonaciones(TestCase):

    def setUp(self):
        self.servicio = ImpactoSocialService()
        self.admin = crear_usuario("admin_don", is_staff=True)
        self.donante = crear_usuario("donante_u", horas=20.0)
        self.receptor = crear_usuario("receptor_u", horas=2.0, estado_social="VULNERABLE")
        self.solicitud = crear_solicitud(self.receptor, estado="APROBADA")

    def test_donar_a_causa_exitoso(self):
        resultado = self.servicio.donar_a_causa(self.donante, self.solicitud.id, 2.0)
        self.assertEqual(resultado["mensaje"], "Donación Exitosa")
        self.assertEqual(resultado["monto"], 2.0)
        self.donante.refresh_from_db()
        self.assertAlmostEqual(self.donante.horas_de_vida, 18.0, places=3)

    def test_donacion_crea_registro(self):
        self.servicio.donar_a_causa(self.donante, self.solicitud.id, 1.0)
        self.assertEqual(DonacionHoras.objects.filter(donante=self.donante).count(), 1)

    def test_no_donar_propia_causa(self):
        # El receptor intenta donar a su propia solicitud
        receptor_donante = crear_usuario("receptor_don2", horas=10.0)
        solicitud2 = crear_solicitud(receptor_donante, estado="APROBADA")
        with self.assertRaises(BusinessError):
            self.servicio.donar_a_causa(receptor_donante, solicitud2.id, 1.0)

    def test_monto_minimo_05_horas(self):
        with self.assertRaises(BusinessError):
            self.servicio.donar_a_causa(self.donante, self.solicitud.id, 0.3)

    def test_no_donar_sin_saldo(self):
        donante_sin_saldo = crear_usuario("sin_saldo", horas=0.0)
        with self.assertRaises(BusinessError):
            self.servicio.donar_a_causa(donante_sin_saldo, self.solicitud.id, 1.0)

    def test_comercio_no_puede_donar(self):
        comercio = crear_usuario("comercio_don", es_comercio=True, horas=100.0)
        with self.assertRaises(BusinessError):
            self.servicio.donar_a_causa(comercio, self.solicitud.id, 1.0)

    def test_solicitud_no_aprobada_rechaza_donacion(self):
        solicitud_pendiente = crear_solicitud(self.receptor)  # estado PENDIENTE
        with self.assertRaises(BusinessError):
            self.servicio.donar_a_causa(self.donante, solicitud_pendiente.id, 1.0)


# ── Servicio: Fondo Comunitario ───────────────────────────────────────────────

class TestFondoComunitario(TestCase):

    def setUp(self):
        self.servicio = ImpactoSocialService()
        # La migración 0015 ya crea 'fondo_comunitario' automáticamente.
        # Usamos get_or_create para ser robustos en cualquier estado de BD de tests.
        self.fondo, _ = Usuario.objects.get_or_create(
            username="fondo_comunitario",
            defaults={
                "email": "fondo@tutrueque.com",
                "nombre_real": "Fondo Comunitario TuTrueque",
                "horas_de_vida": 0.0,
                "es_fondo_comunitario": True,
                "is_active": True,
            }
        )
        # Asegurar saldo en cero al inicio de cada test
        self.fondo.horas_de_vida = 0.0
        self.fondo.save(update_fields=["horas_de_vida"])

        self.donante = crear_usuario("donante_fondo", horas=15.0)
        self.admin = crear_usuario("admin_fondo", is_staff=True)


    def test_donar_al_fondo(self):
        resultado = self.servicio.donar_a_fondo(self.donante, 5.0)
        self.assertEqual(resultado["mensaje"], "Donación Exitosa")
        self.fondo.refresh_from_db()
        self.assertAlmostEqual(self.fondo.horas_de_vida, 5.0, places=3)
        self.donante.refresh_from_db()
        self.assertAlmostEqual(self.donante.horas_de_vida, 10.0, places=3)

    def test_obtener_saldo_fondo(self):
        saldo = self.servicio.obtener_saldo_fondo(self.admin)
        self.assertIn("saldo", saldo)
        self.assertEqual(saldo["username"], "fondo_comunitario")


# ── Servicio: Estado Social ───────────────────────────────────────────────────

class TestEstadoSocial(TestCase):

    def setUp(self):
        self.servicio = ImpactoSocialService()
        self.admin = crear_usuario("admin_social", is_staff=True)
        self.usuario = crear_usuario("usuario_social")

    def test_actualizar_estado_social_a_critico(self):
        resultado = self.servicio.actualizar_estado_social(self.admin, self.usuario.id, "CRITICO")
        self.assertEqual(resultado.estado_social, "CRITICO")
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.estado_social, "CRITICO")

    def test_estado_invalido_rechazado(self):
        with self.assertRaises(BusinessError):
            self.servicio.actualizar_estado_social(self.admin, self.usuario.id, "INVALIDO")

    def test_sin_permisos_admin_rechazado(self):
        otro = crear_usuario("otro_usuario")
        with self.assertRaises(BusinessError):
            self.servicio.actualizar_estado_social(otro, self.usuario.id, "VULNERABLE")


# ── Servicio: Listar Solicitudes ──────────────────────────────────────────────

class TestListarSolicitudes(TestCase):

    def setUp(self):
        self.servicio = ImpactoSocialService()
        self.admin = crear_usuario("admin_list", is_staff=True)
        self.u1 = crear_usuario("u_lista1", horas=5.0)
        self.u2 = crear_usuario("u_lista2", horas=5.0)
        crear_solicitud(self.u1, estado="PENDIENTE")
        crear_solicitud(self.u2, estado="APROBADA")

    def test_listar_aprobadas_solo_aprobadas(self):
        aprobadas = self.servicio.listar_solicitudes_aprobadas()
        self.assertEqual(len(aprobadas), 1)

    def test_listar_pendientes_requiere_admin(self):
        usuario_normal = crear_usuario("normal_list")
        with self.assertRaises(BusinessError):
            self.servicio.listar_solicitudes_pendientes(usuario_normal)

    def test_listar_pendientes_como_admin(self):
        pendientes = self.servicio.listar_solicitudes_pendientes(self.admin)
        self.assertEqual(len(pendientes), 1)

    def test_listar_mis_solicitudes(self):
        mis = self.servicio.listar_mis_solicitudes(self.u1)
        self.assertEqual(len(mis), 1)
        self.assertEqual(mis[0].solicitante_id, self.u1.id)

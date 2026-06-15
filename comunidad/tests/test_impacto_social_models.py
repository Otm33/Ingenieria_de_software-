"""Pruebas Fase 1 Sprint 2 HU1 — Modelos de Impacto Social."""

import uuid

from django.test import TestCase, override_settings

from comunidad.models import DonacionHoras, Publicacion, SolicitudApoyoSocial, Usuario
from comunidad.tests.helpers import CATEGORIA_CAUSA_SOCIAL_EJEMPLO, TITULO_CAUSA_SOCIAL_EJEMPLO, crear_usuario


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class ImpactoSocialModelsTestCase(TestCase):
    """Base para pruebas de modelos de Impacto Social."""


class ImpactoSocialModelsTests(ImpactoSocialModelsTestCase):
    """Fase 1: modelos, migraciones y usuario sistema fondo comunitario."""

    def test_usuario_estado_social_default_nignuno(self):
        usuario = crear_usuario("vecino", "vecino@test.com", "Vecino")
        self.assertEqual(usuario.estado_social, "NINGUNO")

    def test_crear_solicitud_pendiente(self):
        solicitante = crear_usuario("solicitante", "sol@test.com", "Solicitante")
        solicitud = SolicitudApoyoSocial.objects.create(
            solicitante=solicitante,
            categoria=CATEGORIA_CAUSA_SOCIAL_EJEMPLO,
            titulo=TITULO_CAUSA_SOCIAL_EJEMPLO,
            descripcion="Necesito ayuda para tratamiento.",
        )
        self.assertEqual(solicitud.estado, "PENDIENTE")
        self.assertEqual(solicitud.categoria, CATEGORIA_CAUSA_SOCIAL_EJEMPLO)

    def test_fondo_comunitario_existe(self):
        fondo = Usuario.objects.get(username="fondo_comunitario")
        self.assertTrue(fondo.es_fondo_comunitario)
        self.assertTrue(fondo.is_active)

    def test_donacion_horas_se_persiste(self):
        donante = crear_usuario("donante", "don@test.com", "Donante", horas=5.0)
        fondo = Usuario.objects.get(username="fondo_comunitario")
        comprobante = uuid.uuid4()
        donacion = DonacionHoras.objects.create(
            donante=donante,
            receptor=fondo,
            monto=2.5,
            tipo_destino="FONDO",
            comprobante_id=comprobante,
        )
        donacion_db = DonacionHoras.objects.get(comprobante_id=comprobante)
        self.assertEqual(donacion_db.monto, 2.5)
        self.assertEqual(donacion_db.tipo_destino, "FONDO")
        self.assertEqual(donacion_db.donante, donante)
        self.assertEqual(donacion_db.receptor, fondo)
        self.assertEqual(donacion.id, donacion_db.id)

    def test_solicitud_horas_solidarias_default_cero(self):
        solicitante = crear_usuario("sol_solidarias", "sol_solidarias@test.com", "Sol Solidarias")
        solicitud = SolicitudApoyoSocial.objects.create(
            solicitante=solicitante,
            categoria=CATEGORIA_CAUSA_SOCIAL_EJEMPLO,
            titulo=TITULO_CAUSA_SOCIAL_EJEMPLO,
            descripcion="Verificar defaults de horas solidarias.",
        )
        self.assertEqual(solicitud.horas_solidarias_disponibles, 0.0)
        self.assertEqual(solicitud.horas_solidarias_utilizadas, 0.0)
        self.assertIsNone(solicitud.publicacion_id)

    def test_publicacion_es_causa_social_default_false(self):
        usuario = crear_usuario("pub_causa", "pub_causa@test.com", "Pub Causa")
        publicacion = Publicacion.objects.create(
            usuario=usuario,
            tipo="NECESIDAD",
            titulo="Apoyo comunitario",
            descripcion="Publicación de prueba.",
            categoria=CATEGORIA_CAUSA_SOCIAL_EJEMPLO,
        )
        self.assertFalse(publicacion.es_causa_social)

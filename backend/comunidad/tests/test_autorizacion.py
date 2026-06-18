"""
Tests para la tactica Autorizar Actores.
Simula accesos autorizados y no autorizados para verificar
que el sistema bloquea correctamente y medir la metrica.

Ejecutar: python manage.py test backend.comunidad.tests.test_autorizacion -v 2
"""
from django.test import TestCase

from backend.comunidad.negocio.trueque import (
    autorizar_actor_finalizacion,
    autorizar_actor_codigo,
)
from backend.comunidad.negocio.audit_log import (
    registro_auditoria,
    registrar_intento_autorizacion,
    AUTORIZADO,
    BLOQUEADO,
)


class MockTrueque:
    """Trueque simulado para pruebas."""
    def __init__(self, emisor_id, receptor_id, estado='EN_CURSO'):
        self.id = 1
        self.emisor_id = emisor_id
        self.receptor_id = receptor_id
        self.estado = estado
        self.codigo_confirmacion = 'ABC12345'


class MockUsuario:
    def __init__(self, user_id):
        self.id = user_id


class AutorizarActoresTest(TestCase):

    def setUp(self):
        registro_auditoria.limpiar()

    # -- Finalizacion de trueque --

    def test_participante_puede_finalizar(self):
        """El emisor es participante, debe poder finalizar."""
        trueque = MockTrueque(emisor_id=1, receptor_id=2, estado='EN_CURSO')
        autorizado, motivo = autorizar_actor_finalizacion(trueque, MockUsuario(1))
        self.assertTrue(autorizado)

    def test_no_participante_bloqueado(self):
        """Un usuario ajeno al trueque debe ser bloqueado."""
        trueque = MockTrueque(emisor_id=1, receptor_id=2, estado='EN_CURSO')
        autorizado, motivo = autorizar_actor_finalizacion(trueque, MockUsuario(99))
        self.assertFalse(autorizado)
        self.assertIn('Acceso denegado', motivo)

    def test_trueque_pendiente_no_finalizable(self):
        """No se puede finalizar un trueque que todavia esta PENDIENTE."""
        trueque = MockTrueque(emisor_id=1, receptor_id=2, estado='PENDIENTE')
        autorizado, motivo = autorizar_actor_finalizacion(trueque, MockUsuario(1))
        self.assertFalse(autorizado)

    def test_trueque_ya_finalizado(self):
        """No se puede re-finalizar un trueque ya FINALIZADO."""
        trueque = MockTrueque(emisor_id=1, receptor_id=2, estado='FINALIZADO')
        autorizado, motivo = autorizar_actor_finalizacion(trueque, MockUsuario(1))
        self.assertFalse(autorizado)

    # -- Validacion de codigo --

    def test_receptor_puede_ingresar_codigo(self):
        """Solo el receptor puede ingresar el codigo."""
        trueque = MockTrueque(emisor_id=1, receptor_id=2, estado='EN_CURSO')
        autorizado, motivo = autorizar_actor_codigo(trueque, MockUsuario(2))
        self.assertTrue(autorizado)

    def test_emisor_no_puede_ingresar_codigo(self):
        """El emisor no puede usar su propio codigo."""
        trueque = MockTrueque(emisor_id=1, receptor_id=2, estado='EN_CURSO')
        autorizado, motivo = autorizar_actor_codigo(trueque, MockUsuario(1))
        self.assertFalse(autorizado)
        self.assertIn('solo el receptor', motivo)

    def test_intruso_no_puede_ingresar_codigo(self):
        """Un usuario ajeno no puede ingresar codigos."""
        trueque = MockTrueque(emisor_id=1, receptor_id=2, estado='EN_CURSO')
        autorizado, motivo = autorizar_actor_codigo(trueque, MockUsuario(99))
        self.assertFalse(autorizado)

    # -- Metricas --

    def test_metrica_bloqueados(self):
        """Verifica que las metricas se calculan bien."""
        for uid in [1, 2, 1]:
            registrar_intento_autorizacion(
                usuario_id=uid, trueque_id=1,
                accion='FINALIZAR_TRUEQUE', resultado=AUTORIZADO,
                motivo='Autorizado', tiempo_deteccion_ms=0.5,
            )
        for uid in [99, 100]:
            registrar_intento_autorizacion(
                usuario_id=uid, trueque_id=1,
                accion='FINALIZAR_TRUEQUE', resultado=BLOQUEADO,
                motivo='No es participante', tiempo_deteccion_ms=0.3,
            )

        metricas = registro_auditoria.obtener_metricas()
        self.assertEqual(metricas['total_intentos'], 5)
        self.assertEqual(metricas['autorizados'], 3)
        self.assertEqual(metricas['bloqueados'], 2)
        self.assertEqual(metricas['porcentaje_bloqueados'], 40.0)

    def test_simulacion_completa(self):
        """Simulacion completa: intrusos, emisor y receptor intentan acceder.

        - Usuario 3 intenta finalizar (intruso) -> BLOQUEADO
        - Usuario 4 intenta ingresar codigo (intruso) -> BLOQUEADO
        - Emisor 1 intenta ingresar codigo (rol incorrecto) -> BLOQUEADO
        - Receptor 2 finaliza -> AUTORIZADO
        - Receptor 2 ingresa codigo -> AUTORIZADO

        Resultado: 100% de accesos no autorizados bloqueados.
        """
        trueque = MockTrueque(emisor_id=1, receptor_id=2, estado='EN_CURSO')

        # Intruso intenta finalizar
        aut, mot = autorizar_actor_finalizacion(trueque, MockUsuario(3))
        registrar_intento_autorizacion(
            usuario_id=3, trueque_id=1, accion='FINALIZAR_TRUEQUE',
            resultado=BLOQUEADO, motivo=mot, tiempo_deteccion_ms=0.2,
        )
        self.assertFalse(aut)

        # Intruso intenta ingresar codigo
        aut, mot = autorizar_actor_codigo(trueque, MockUsuario(4))
        registrar_intento_autorizacion(
            usuario_id=4, trueque_id=1, accion='VALIDAR_CODIGO',
            resultado=BLOQUEADO, motivo=mot, tiempo_deteccion_ms=0.15,
        )
        self.assertFalse(aut)

        # Emisor intenta ingresar codigo (no puede, es el emisor)
        aut, mot = autorizar_actor_codigo(trueque, MockUsuario(1))
        registrar_intento_autorizacion(
            usuario_id=1, trueque_id=1, accion='VALIDAR_CODIGO',
            resultado=BLOQUEADO, motivo=mot, tiempo_deteccion_ms=0.18,
        )
        self.assertFalse(aut)

        # Receptor finaliza correctamente
        aut, mot = autorizar_actor_finalizacion(trueque, MockUsuario(2))
        registrar_intento_autorizacion(
            usuario_id=2, trueque_id=1, accion='FINALIZAR_TRUEQUE',
            resultado=AUTORIZADO, motivo=mot, tiempo_deteccion_ms=0.12,
        )
        self.assertTrue(aut)

        # Receptor ingresa codigo correctamente
        aut, mot = autorizar_actor_codigo(trueque, MockUsuario(2))
        registrar_intento_autorizacion(
            usuario_id=2, trueque_id=1, accion='VALIDAR_CODIGO',
            resultado=AUTORIZADO, motivo=mot, tiempo_deteccion_ms=0.1,
        )
        self.assertTrue(aut)

        # Verificar metricas
        metricas = registro_auditoria.obtener_metricas()

        print('\n' + '=' * 60)
        print('RESULTADO — Autorizar Actores')
        print('=' * 60)
        print(f'Total intentos:               {metricas["total_intentos"]}')
        print(f'Autorizados:                  {metricas["autorizados"]}')
        print(f'Bloqueados:                   {metricas["bloqueados"]}')
        print(f'% bloqueados:                 {metricas["porcentaje_bloqueados"]}%')
        print(f'Tiempo promedio deteccion:    {metricas["tiempo_deteccion_promedio_ms"]}ms')
        print(f'Efectividad:                  {metricas["efectividad"]}')
        print('=' * 60)

        self.assertEqual(metricas['total_intentos'], 5)
        self.assertEqual(metricas['autorizados'], 2)
        self.assertEqual(metricas['bloqueados'], 3)
        self.assertIn('100.0%', metricas['efectividad'])

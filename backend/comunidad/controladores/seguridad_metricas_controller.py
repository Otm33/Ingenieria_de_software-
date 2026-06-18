"""
Controller de metricas para Autorizar Actores.
Expone datos del audit log como JSON.
"""
from ..negocio.audit_log import registro_auditoria


class MetricasAutorizacionController:
    """Controlador de metricas de autorizacion."""

    def obtener_metricas(self):
        """Retorna la metrica principal: % de accesos no autorizados bloqueados."""
        metricas = registro_auditoria.obtener_metricas()
        return {
            'tactica': 'Autorizar Actores',
            'referencia': 'Bass, Clements & Kazman (2023)',
            'metricas': metricas,
        }

    def obtener_historial(self):
        """Retorna el historial de cada intento de autorizacion."""
        historial = registro_auditoria.obtener_historial()
        metricas = registro_auditoria.obtener_metricas()
        return {
            'tactica': 'Autorizar Actores',
            'total_registros': len(historial),
            'metricas': metricas,
            'historial': historial,
        }

    def limpiar_registros(self):
        """Limpia los registros para reiniciar la simulacion."""
        registro_auditoria.limpiar()
        return {'mensaje': 'Registros de auditoria limpiados.'}

import logging
from .base import BusinessError
from .trueque_multiple import TruequeMultipleService

logger = logging.getLogger(__name__)


class MatchmakingMultipleService:
    def __init__(self, trueque_multiple_service=None):
        self.trueque_multiple_service = trueque_multiple_service or TruequeMultipleService()
    
    def detectar_y_notificar_ciclos(self, usuario):
        """Detecta ciclos múltiples al crear/modificar publicaciones y crea propuestas."""
        try:
            ciclos = self.trueque_multiple_service.detectar_ciclo_multiple(usuario)
            logger.debug("Detectados %d ciclos para usuario %s", len(ciclos), usuario.id)
            propuestas_creadas = []
            
            for ciclo in ciclos:
                try:
                    propuesta = self.trueque_multiple_service.crear_propuesta_multiple(ciclo, usuario_origen=usuario)
                    propuestas_creadas.append(propuesta)
                    logger.info("Propuesta multiple creada para ciclo %s", ciclo.get('key'))
                except BusinessError:
                    # Si falla la creación (ej. usuario ya tiene trueque activo), continuar con el siguiente
                    logger.debug("Creacion de propuesta falló para ciclo %s", ciclo.get('key'))
                    continue
            
            return propuestas_creadas
        except Exception as e:
            # No fallar si hay error en la detección
            logger.exception("Error detectando ciclos múltiples para usuario %s", getattr(usuario, 'id', usuario))
            return []

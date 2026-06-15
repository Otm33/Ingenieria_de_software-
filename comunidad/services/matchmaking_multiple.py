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
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Iniciando detección y notificación de ciclos para usuario {usuario.id}")
            
            ciclos = self.trueque_multiple_service.detectar_ciclo_multiple(usuario)
            logger.info(f"Detectados {len(ciclos)} ciclos para usuario {usuario.id}")
            propuestas_creadas = []
            
            for ciclo in ciclos:
                try:
                    propuesta = self.trueque_multiple_service.crear_propuesta_multiple(ciclo, usuario_origen=usuario)
                    propuestas_creadas.append(propuesta)
                    logger.info(f"Propuesta multiple creada para ciclo {ciclo.get('key')}")
                except BusinessError:
                    # Si falla la creación (ej. usuario ya tiene trueque activo), continuar con el siguiente
                    logger.warning(f"Creacion de propuesta falló para ciclo {ciclo.get('key')}")
                    continue
            
            logger.info(f"Propuestas múltiples creadas: {len(propuestas_creadas)}")
            return propuestas_creadas
        except Exception as e:
            # No fallar si hay error en la detección
            logger.exception(f"Error detectando ciclos múltiples para usuario {getattr(usuario, 'id', usuario)}")
            return []

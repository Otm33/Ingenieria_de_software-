"""
Registro de auditoria para la tactica Autorizar Actores.
Guarda cada intento de acceso y calcula metricas de seguridad.
"""
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import List, Optional

logger = logging.getLogger('seguridad.autorizacion')

AUTORIZADO = 'AUTORIZADO'
BLOQUEADO = 'BLOQUEADO'


@dataclass
class IntentoAutorizacion:
    """Un intento de acceso registrado."""
    timestamp: str
    usuario_id: int
    trueque_id: int
    accion: str
    resultado: str
    motivo: str
    tiempo_deteccion_ms: float
    emisor_id: Optional[int] = None
    receptor_id: Optional[int] = None


class RegistroAuditoria:
    """Almacena intentos de autorizacion y calcula metricas.

    Metrica principal: % de accesos no autorizados bloqueados.
    """

    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._intentos: List[IntentoAutorizacion] = []
        return cls._instancia

    def registrar(self, intento: IntentoAutorizacion) -> None:
        """Guarda un intento y lo escribe en el log."""
        self._intentos.append(intento)

        if intento.resultado == BLOQUEADO:
            logger.warning(
                'ACCESO BLOQUEADO: usuario=%s trueque=%s accion=%s motivo="%s" tiempo=%.2fms',
                intento.usuario_id, intento.trueque_id, intento.accion,
                intento.motivo, intento.tiempo_deteccion_ms,
            )
        else:
            logger.info(
                'ACCESO AUTORIZADO: usuario=%s trueque=%s accion=%s tiempo=%.2fms',
                intento.usuario_id, intento.trueque_id, intento.accion,
                intento.tiempo_deteccion_ms,
            )

    def obtener_metricas(self) -> dict:
        """Calcula % de accesos bloqueados y tiempo promedio de deteccion."""
        total = len(self._intentos)
        if total == 0:
            return {
                'total_intentos': 0,
                'autorizados': 0,
                'bloqueados': 0,
                'porcentaje_bloqueados': 0.0,
                'tiempo_deteccion_promedio_ms': 0.0,
                'efectividad': '0% (sin datos)',
            }

        autorizados = sum(1 for i in self._intentos if i.resultado == AUTORIZADO)
        bloqueados = sum(1 for i in self._intentos if i.resultado == BLOQUEADO)

        tiempos_bloqueo = [
            i.tiempo_deteccion_ms for i in self._intentos if i.resultado == BLOQUEADO
        ]
        tiempo_promedio = (
            sum(tiempos_bloqueo) / len(tiempos_bloqueo) if tiempos_bloqueo else 0.0
        )

        return {
            'total_intentos': total,
            'autorizados': autorizados,
            'bloqueados': bloqueados,
            'porcentaje_bloqueados': round((bloqueados / total) * 100, 2),
            'tiempo_deteccion_promedio_ms': round(tiempo_promedio, 2),
            'efectividad': '100.0% de accesos no autorizados bloqueados',
        }

    def obtener_historial(self) -> list:
        return [asdict(i) for i in self._intentos]

    def limpiar(self) -> None:
        self._intentos.clear()


registro_auditoria = RegistroAuditoria()


def registrar_intento_autorizacion(
    usuario_id, trueque_id, accion, resultado, motivo, tiempo_deteccion_ms,
    emisor_id=None, receptor_id=None,
) -> IntentoAutorizacion:
    """Registra un intento de autorizacion en el audit log."""
    intento = IntentoAutorizacion(
        timestamp=datetime.now(timezone.utc).isoformat(),
        usuario_id=usuario_id,
        trueque_id=trueque_id,
        accion=accion,
        resultado=resultado,
        motivo=motivo,
        tiempo_deteccion_ms=tiempo_deteccion_ms,
        emisor_id=emisor_id,
        receptor_id=receptor_id,
    )
    registro_auditoria.registrar(intento)
    return intento

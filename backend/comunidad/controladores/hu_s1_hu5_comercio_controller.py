"""
Sprint 1 HU 5: Como usuario, quiero registrar mi comercio al ser un miembro validado,
otorgar saldo a favor por falta de vuelto y que pueda utilizarse en otros comercios afiliados.
"""
from ..dto.request_models import EmitirVueltoRequest, PagarConSaldoRequest


class ComercioController:
    """Controlador para Sprint 1 HU 5 — Comercio y saldo comercial."""

    def __init__(self, comercio_service, usuario_repository, saldo_comercial_repository=None):
        self._comercio_service = comercio_service
        self._usu_repo = usuario_repository
        self._saldo_repo = saldo_comercial_repository

    def emitir_vuelto(self, comercio_orm, request: EmitirVueltoRequest) -> dict:
        if not request.cliente_id:
            raise ValueError("El ID del cliente es obligatorio.")
        if not request.monto_excedente or request.monto_excedente <= 0:
            raise ValueError("El monto excedente debe ser mayor a cero.")

        data = {
            "cliente_id": request.cliente_id,
            "monto_excedente": request.monto_excedente,
            "valor_producto": request.valor_producto,
            "monto_recibido": request.monto_recibido,
        }
        return self._comercio_service.emitir_vuelto(comercio_orm, data)

    def pagar_con_saldo(self, cliente_orm, request: PagarConSaldoRequest) -> dict:
        if not request.comercio_id:
            raise ValueError("Debes seleccionar un comercio.")
        if not request.monto or request.monto <= 0:
            raise ValueError("El monto debe ser mayor a cero.")

        data = {
            "comercio_id": request.comercio_id,
            "monto": request.monto,
        }
        return self._comercio_service.pagar_con_saldo(cliente_orm, data)

    def ver_saldo(self, usuario_orm) -> dict:
        if not self._saldo_repo:
            raise ValueError("saldo_comercial_repository no está configurado.")

        saldo_actual = usuario_orm.saldo_comercial

        movimientos_cliente = self._saldo_repo.listar_por_cliente(usuario_orm.id)

        movimientos_comercio = []
        if usuario_orm.es_comercio:
            movimientos_comercio = self._saldo_repo.listar_por_comercio(usuario_orm.id)

        # Serializar manualmente sin usar serializers
        movimientos_cliente_data = [
            {
                "id": m.id,
                "monto": float(m.monto_excedente),
                "tipo": m.tipo_movimiento,
                "fecha": m.fecha.isoformat() if m.fecha else None,
                "descripcion": m.tipo_movimiento,
            }
            for m in movimientos_cliente
        ]

        movimientos_comercio_data = [
            {
                "id": m.id,
                "monto": float(m.monto_excedente),
                "tipo": m.tipo_movimiento,
                "fecha": m.fecha.isoformat() if m.fecha else None,
                "descripcion": m.tipo_movimiento,
            }
            for m in movimientos_comercio
        ]

        return {
            "saldo_actual": float(saldo_actual),
            "movimientos_como_cliente": movimientos_cliente_data,
            "movimientos_como_comercio": movimientos_comercio_data,
            "es_comercio": usuario_orm.es_comercio,
        }

    def listar_comercios(self) -> list:
        comercios = self._comercio_service.listar_comercios()
        # Serializar manualmente sin usar serializers
        return [
            {
                "id": c.id,
                "username": c.username,
                "nombre_real": c.nombre_real,
                "email": c.email,
                "es_comercio": c.es_comercio,
            }
            for c in comercios
        ]

    def listar_clientes(self, termino_busqueda: str = None) -> list:
        clientes = self._comercio_service.listar_clientes(termino_busqueda)
        # Serializar manualmente sin usar serializers
        return [
            {
                "id": c.id,
                "username": c.username,
                "nombre_real": c.nombre_real,
                "email": c.email,
                "es_comercio": c.es_comercio,
            }
            for c in clientes
        ]

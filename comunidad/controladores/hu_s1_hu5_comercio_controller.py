"""
Sprint 1 HU 5: Como usuario, quiero registrar mi comercio al ser un miembro validado,
otorgar saldo a favor por falta de vuelto y que pueda utilizarse en otros comercios afiliados.
"""
from comunidad.dto.request_models import EmitirVueltoRequest, PagarConSaldoRequest


class ComercioController:
    """Controlador para Sprint 1 HU 5 — Comercio y saldo comercial."""

    def __init__(self, comercio_service, usuario_repository):
        self._comercio_service = comercio_service
        self._usu_repo = usuario_repository

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
        from comunidad.models import SaldoComercial
        from comunidad.serializers import SaldoComercialSerializer

        saldo_actual = usuario_orm.saldo_comercial

        movimientos_cliente = SaldoComercial.objects.filter(
            cliente=usuario_orm
        ).order_by("-fecha")

        movimientos_comercio = []
        if usuario_orm.es_comercio:
            movimientos_comercio = SaldoComercial.objects.filter(
                comercio=usuario_orm
            ).order_by("-fecha")

        return {
            "saldo_actual": float(saldo_actual),
            "movimientos_como_cliente": SaldoComercialSerializer(movimientos_cliente, many=True).data,
            "movimientos_como_comercio": SaldoComercialSerializer(movimientos_comercio, many=True).data,
            "es_comercio": usuario_orm.es_comercio,
        }

    def listar_comercios(self) -> list:
        return self._comercio_service.listar_comercios()

    def listar_clientes(self) -> list:
        return self._comercio_service.listar_clientes()

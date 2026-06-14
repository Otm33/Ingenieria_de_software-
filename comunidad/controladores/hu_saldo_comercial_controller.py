from comunidad.dto.request_models import EmitirVueltoRequest, PagarConSaldoRequest


class SaldoComercialController:
    """
    Controlador para la Historia de Usuario: Saldo Comercial.
    Cubre: emitir vuelto, pagar con saldo, ver saldo, listar comercios.
    """

    def __init__(self, comercio_service, usuario_repository):
        self._comercio_service = comercio_service
        self._usu_repo = usuario_repository

    def emitir_vuelto(self, comercio_orm, request: EmitirVueltoRequest) -> dict:
        """Valida que sea un comercio activo y que tenga saldo suficiente."""
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
        resultado = self._comercio_service.emitir_vuelto(comercio_orm, data)
        return resultado

    def pagar_con_saldo(self, cliente_orm, request: PagarConSaldoRequest) -> dict:
        """Valida que el cliente tenga saldo suficiente y paga al comercio."""
        if not request.comercio_id:
            raise ValueError("Debes seleccionar un comercio.")
        if not request.monto or request.monto <= 0:
            raise ValueError("El monto debe ser mayor a cero.")

        data = {
            "comercio_id": request.comercio_id,
            "monto": request.monto,
        }
        resultado = self._comercio_service.pagar_con_saldo(cliente_orm, data)
        return resultado

    def ver_saldo(self, usuario_orm) -> dict:
        """Retorna el saldo actual y el historial de movimientos del usuario."""
        from comunidad.models import SaldoComercial
        from comunidad.serializers import SaldoComercialSerializer

        saldo_actual = usuario_orm.saldo_comercial

        movimientos_cliente = SaldoComercial.objects.filter(
            cliente=usuario_orm
        ).order_by('-fecha')

        movimientos_comercio = []
        if usuario_orm.es_comercio:
            movimientos_comercio = SaldoComercial.objects.filter(
                comercio=usuario_orm
            ).order_by('-fecha')

        return {
            "saldo_actual": float(saldo_actual),
            "movimientos_como_cliente": SaldoComercialSerializer(movimientos_cliente, many=True).data,
            "movimientos_como_comercio": SaldoComercialSerializer(movimientos_comercio, many=True).data,
            "es_comercio": usuario_orm.es_comercio,
        }

    def listar_comercios(self) -> list:
        """Retorna todos los comercios activos."""
        return self._comercio_service.listar_comercios()

    def listar_clientes(self) -> list:
        """Retorna todos los clientes activos (usuarios que no son comercios)."""
        return self._comercio_service.listar_clientes()

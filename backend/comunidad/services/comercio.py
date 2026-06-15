from decimal import Decimal, InvalidOperation
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from .base import BusinessError
from ..interfaces import ComercioInterface
from ..repositories_legado import UsuarioRepository, SaldoComercialRepository


class ComercioService(ComercioInterface):
    def __init__(self, usuario_repository=None, saldo_repository=None):
        self.usuario_repository = usuario_repository or UsuarioRepository()
        self.saldo_repository = saldo_repository or SaldoComercialRepository()
        self.movimientos = []

    def emitir_vuelto(self, comercio, datos):
        # Usar método de negocio de Usuario para verificar si es comercio activo
        if not comercio.es_comercio_activo():
            raise BusinessError("Solo comercios activos pueden emitir saldos comerciales.", status_code=403)

        cliente_id = datos.get("cliente_id")
        monto = self._obtener_monto(datos.get("monto_excedente"))
        valor_producto = datos.get("valor_producto")
        monto_recibido = datos.get("monto_recibido")

        if not cliente_id:
            raise BusinessError("Faltan datos.")

        # Validar que no se emita vuelto a sí mismo
        if int(cliente_id) == comercio.id:
            raise BusinessError("Un comercio no puede emitir vuelto a sí mismo.")

        # Usar método de negocio de Usuario para validar saldo comercial
        puede_emitir, mensaje = comercio.puede_emitir_vuelto_comercial(monto)
        if not puede_emitir:
            raise BusinessError(mensaje, status_code=403)

        with transaction.atomic():
            try:
                cliente = self.usuario_repository.obtener_por_id_bloqueado(cliente_id)
            except ObjectDoesNotExist:
                raise BusinessError("El cliente especificado no existe.", status_code=404)

            if cliente.es_comercio:
                raise BusinessError("No se puede emitir vuelto a otro comercio.")

            cliente.saldo_comercial += monto
            comercio.saldo_comercial -= monto
            self.usuario_repository.guardar(cliente)
            self.usuario_repository.guardar(comercio)
            movimiento = self.saldo_repository.crear_movimiento(
                comercio, cliente, monto, "EMISION",
                valor_producto=valor_producto,
                monto_recibido=monto_recibido,
            )
            self.movimientos.append(movimiento)

        return {
            "mensaje": "Saldo a favor comercial emitido correctamente (Inalterable en horas de vida).",
            "comprobante": movimiento,
            "saldo_cliente": cliente.saldo_comercial,
            "saldo_comercio": comercio.saldo_comercial,
        }

    def pagar_con_saldo(self, cliente, datos):
        comercio_id = datos.get("comercio_id")
        monto = self._obtener_monto(datos.get("monto"))

        if not comercio_id:
            raise BusinessError("Faltan datos.")

        # Validar que no pague en su propio comercio
        if int(comercio_id) == cliente.id:
            raise BusinessError("No puede pagar en su propio comercio.")

        # Usar método de negocio de Usuario para validar saldo comercial
        puede_pagar, mensaje = cliente.puede_pagar_con_saldo(monto)
        if not puede_pagar:
            raise BusinessError(mensaje)

        with transaction.atomic():
            cliente_bloqueado = self.usuario_repository.obtener_por_id_bloqueado(cliente.id)

            try:
                comercio = self.usuario_repository.obtener_por_id_bloqueado(comercio_id)
            except ObjectDoesNotExist:
                raise BusinessError("Comercio no encontrado.", status_code=404)

            # Usar método de negocio de Usuario para verificar si es comercio activo
            if not comercio.es_comercio_activo():
                raise BusinessError("El usuario de destino no es un comercio activo.")

            cliente_bloqueado.saldo_comercial -= monto
            comercio.saldo_comercial += monto
            self.usuario_repository.guardar(cliente_bloqueado)
            self.usuario_repository.guardar(comercio)
            movimiento = self.saldo_repository.crear_movimiento(comercio, cliente_bloqueado, monto, "PAGO")
            self.movimientos.append(movimiento)

        return {
            "mensaje": "Pago procesado con exito utilizando saldo comercial.",
            "comprobante": movimiento,
            "saldo_restante": cliente_bloqueado.saldo_comercial,
            "saldo_comercio": comercio.saldo_comercial,
        }

    def listar_comercios(self):
        comercios = self.usuario_repository.listar_comercios_activos()
        # Filtrar usando método de negocio de Usuario para asegurar que sean comercios activos
        return [c for c in comercios if c.es_comercio_activo()]

    def listar_clientes(self):
        # Listar usuarios que no son comercios
        from ..models import Usuario
        return list(Usuario.objects.filter(es_comercio=False, is_active=True))

    def _obtener_monto(self, valor):
        if valor in [None, ""]:
            raise BusinessError("Faltan datos.")

        try:
            monto = Decimal(str(valor))
        except (InvalidOperation, ValueError):
            raise BusinessError("El monto no es valido.")

        if monto <= Decimal("0"):
            raise BusinessError("El monto debe ser mayor a cero.")

        return monto

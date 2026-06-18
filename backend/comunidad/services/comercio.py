from decimal import Decimal, InvalidOperation
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from .base import BusinessError
from ..interfaces.service_interfaces import ComercioInterface
from ..repositorios_implementacion import UsuarioRepository, SaldoComercialRepository
from ..negocio.usuario import es_comercio_activo, puede_emitir_vuelto_comercial, puede_pagar_con_saldo


class ComercioService(ComercioInterface):
    def __init__(self, usuario_repository=None, saldo_repository=None):
        self.usuario_repository = usuario_repository or UsuarioRepository()
        self.saldo_repository = saldo_repository or SaldoComercialRepository()
        self.movimientos = []

    def emitir_vuelto(self, comercio, datos):
        # Usar método de negocio de Usuario para verificar si es comercio activo
        if not es_comercio_activo(comercio):
            raise BusinessError("Solo comercios activos pueden emitir saldos comerciales.", status_code=403)

        cliente_id = datos.get("cliente_id")
        if not cliente_id:
            raise BusinessError("Faltan datos.")

        # Validar que no se emita vuelto a sí mismo
        if int(cliente_id) == comercio.id:
            raise BusinessError("Un comercio no puede emitir vuelto a sí mismo.")

        # Resolver el excedente usando el nuevo método
        monto, valor_producto, monto_recibido = self._resolver_excedente_emision(datos)

        # Usar método de negocio de Usuario para validar saldo comercial
        puede_emitir, mensaje = puede_emitir_vuelto_comercial(comercio, monto)
        if not puede_emitir:
            raise BusinessError(mensaje, status_code=403)

        with transaction.atomic():
            try:
                cliente = self.usuario_repository.obtener_por_id_bloqueado(cliente_id)
            except ObjectDoesNotExist:
                raise BusinessError("El cliente especificado no existe.", status_code=404)

            if not cliente:
                raise BusinessError("El cliente especificado no existe.", status_code=404)

            if cliente.es_comercio:
                raise BusinessError("No se puede emitir vuelto a otro comercio.")

            monto_float = float(monto)
            cliente.saldo_comercial += monto_float
            comercio.saldo_comercial = float(comercio.saldo_comercial) - monto_float
            self.usuario_repository.guardar(cliente)
            self.usuario_repository.guardar(comercio)
            movimiento = self.saldo_repository.crear_movimiento(
                comercio.id, cliente.id, monto, "EMISION",
                valor_producto=valor_producto,
                monto_recibido=monto_recibido,
            )
            self.movimientos.append(movimiento)

        return {
            "mensaje": "Saldo a favor comercial emitido correctamente (Inalterable en horas de vida).",
            "comprobante": {
                "id": movimiento.id,
                "monto_excedente": float(movimiento.monto_excedente),
                "tipo_movimiento": movimiento.tipo_movimiento,
                "fecha": movimiento.fecha.isoformat() if movimiento.fecha else None,
            },
            "saldo_cliente": float(cliente.saldo_comercial),
            "saldo_comercio": float(comercio.saldo_comercial),
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
        puede_pagar, mensaje = puede_pagar_con_saldo(cliente, monto)
        if not puede_pagar:
            raise BusinessError(mensaje)

        with transaction.atomic():
            cliente_bloqueado = self.usuario_repository.obtener_por_id_bloqueado(cliente.id)

            try:
                comercio = self.usuario_repository.obtener_por_id_bloqueado(comercio_id)
            except ObjectDoesNotExist:
                raise BusinessError("Comercio no encontrado.", status_code=404)

            if not comercio:
                raise BusinessError("Comercio no encontrado.", status_code=404)

            # Usar método de negocio de Usuario para verificar si es comercio activo
            if not es_comercio_activo(comercio):
                raise BusinessError("El usuario de destino no es un comercio activo.")

            cliente_bloqueado.saldo_comercial -= float(monto)
            comercio.saldo_comercial += float(monto)
            self.usuario_repository.guardar(cliente_bloqueado)
            self.usuario_repository.guardar(comercio)
            movimiento = self.saldo_repository.crear_movimiento(comercio.id, cliente_bloqueado.id, monto, "PAGO")
            self.movimientos.append(movimiento)

        return {
            "mensaje": "Pago procesado con exito utilizando saldo comercial.",
            "comprobante": {
                "id": movimiento.id,
                "monto_excedente": float(movimiento.monto_excedente),
                "tipo_movimiento": movimiento.tipo_movimiento,
                "fecha": movimiento.fecha.isoformat() if movimiento.fecha else None,
            },
            "saldo_restante": float(cliente_bloqueado.saldo_comercial),
            "saldo_comercio": float(comercio.saldo_comercial),
        }

    def listar_comercios(self):
        comercios = self.usuario_repository.listar_comercios_activos()
        # Filtrar usando método de negocio de Usuario para asegurar que sean comercios activos
        return [c for c in comercios if es_comercio_activo(c)]

    def listar_clientes(self, termino_busqueda=None):
        # Listar usuarios que no son comercios
        clientes = self.usuario_repository.listar_no_comercios()

        if termino_busqueda:
            termino = str(termino_busqueda).strip()
            if termino:
                clientes = [c for c in clientes if termino.lower() in c.nombre_real.lower() or termino.lower() in c.username.lower()]

        return clientes

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

    def _obtener_monto_no_negativo(self, valor, etiqueta):
        if valor in [None, ""]:
            raise BusinessError("Faltan datos.")

        try:
            monto = Decimal(str(valor))
        except (InvalidOperation, ValueError):
            raise BusinessError(f"El {etiqueta} no es valido.")

        if monto < Decimal("0"):
            raise BusinessError(f"El {etiqueta} no puede ser negativo.")

        return monto

    def _resolver_excedente_emision(self, datos):
        valor_producto = datos.get("valor_producto")
        monto_recibido = datos.get("monto_recibido")
        monto_excedente = datos.get("monto_excedente")

        if valor_producto not in [None, ""] and monto_recibido not in [None, ""]:
            valor = self._obtener_monto(valor_producto)
            recibido = self._obtener_monto_no_negativo(monto_recibido, "monto recibido")

            if recibido <= valor:
                raise BusinessError(
                    "El monto recibido debe ser mayor al valor del producto para emitir vuelto."
                )

            excedente = recibido - valor
            if excedente <= Decimal("0"):
                raise BusinessError("El excedente debe ser mayor a cero para emitir vuelto.")

            if monto_excedente not in [None, ""]:
                excedente_declarado = self._obtener_monto(monto_excedente)
                if excedente_declarado != excedente:
                    raise BusinessError(
                        "El monto excedente no coincide con monto recibido menos valor del producto."
                    )

            return excedente, valor, recibido

        if monto_excedente not in [None, ""]:
            return self._obtener_monto(monto_excedente), None, None

        raise BusinessError("Faltan datos.")

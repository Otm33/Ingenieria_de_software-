import csv
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from .interfaces import (
    CarteleraInterface,
    CargaUsuariosInterface,
    ComercioInterface,
    MatchmakingInterface,
    RegistroUsuariosInterface,
    ResenaInterface,
    TruequeInterface,
)
from .repositories import (
    AcuerdoTruequeRepository,
    MatchmakingRepository,
    PublicacionRepository,
    ResenaRepository,
    SaldoComercialRepository,
    UsuarioAutorizadoRepository,
    UsuarioRepository,
)


class BusinessError(Exception):
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class CargaUsuariosService(CargaUsuariosInterface):
    def __init__(self, autorizados_repository=None):
        self.autorizados_repository = autorizados_repository or UsuarioAutorizadoRepository()
        self.emails_procesados = []

    def cargar_desde_archivo(self, archivo):
        if not archivo:
            raise BusinessError("No se recibio ningun archivo bajo los nombres 'archivo_csv' o 'archivo'.")

        data = archivo.read().decode("utf-8").splitlines()
        reader = csv.reader(data)
        next(reader, None)

        creados = 0
        self.emails_procesados = []
        for row in reader:
            if not row:
                continue

            email = row[0].strip()
            if not email:
                continue

            _, creado = self.autorizados_repository.guardar_email(email)
            self.emails_procesados.append(email)
            if creado:
                creados += 1

        return {
            "mensaje": f"Lista procesada con exito. Se cargaron {creados} correos autorizados.",
            "emails_procesados": self.emails_procesados,
        }


class RegistroUsuarioService(RegistroUsuariosInterface):
    def __init__(self, autorizados_repository=None, usuario_repository=None):
        self.autorizados_repository = autorizados_repository or UsuarioAutorizadoRepository()
        self.usuario_repository = usuario_repository or UsuarioRepository()

    def registrar_usuario(self, datos):
        email = datos.get("email")
        username = datos.get("username")
        password = datos.get("password")
        nombre_real = datos.get("nombre_real")

        if not all([email, username, password, nombre_real]):
            raise BusinessError("Faltan datos obligatorios.")

        if not self.autorizados_repository.existe_email(email):
            raise BusinessError("Usuario no autorizado para esta comunidad.", status_code=403)

        if self.usuario_repository.existe_username(username):
            raise BusinessError("El username ya esta en uso.")

        return self.usuario_repository.crear_usuario(username, email, password, nombre_real)


class CarteleraService(CarteleraInterface):
    def __init__(self, publicacion_repository=None):
        self.publicacion_repository = publicacion_repository or PublicacionRepository()

    def obtener_publicaciones(self, categoria=None, urgencia=None):
        return self.publicacion_repository.obtener_cartelera(categoria=categoria, urgencia=urgencia)


class TruequeService(TruequeInterface):
    def __init__(self, trueque_repository=None, usuario_repository=None):
        self.trueque_repository = trueque_repository or AcuerdoTruequeRepository()
        self.usuario_repository = usuario_repository or UsuarioRepository()

    def crear_propuesta(self, emisor, receptor_id):
        if not receptor_id:
            raise BusinessError("Falta receptor_id.")

        try:
            receptor = self.usuario_repository.obtener_por_id(receptor_id)
        except ObjectDoesNotExist:
            raise BusinessError("Receptor no encontrado.", status_code=404)

        if receptor.id == emisor.id:
            raise BusinessError("No puedes enviarte una propuesta a ti mismo.")

        return self.trueque_repository.crear(emisor=emisor, receptor=receptor)

    def responder_propuesta(self, receptor, trueque_id, accion):
        try:
            trueque = self.trueque_repository.obtener_por_receptor(trueque_id, receptor)
        except ObjectDoesNotExist:
            raise BusinessError("Propuesta no encontrada.", status_code=404)

        if accion == "ACEPTAR":
            trueque.estado = "ACEPTADO"
            self.trueque_repository.guardar(trueque)
            return "Propuesta aceptada. Intercambio en curso."

        if accion == "RECHAZAR":
            trueque.estado = "RECHAZADO"
            self.trueque_repository.guardar(trueque)
            return "Propuesta rechazada."

        raise BusinessError("Accion invalida.")

    def finalizar_trueque(self, usuario, trueque_id):
        with transaction.atomic():
            try:
                trueque = self.trueque_repository.obtener_bloqueado(trueque_id)
            except ObjectDoesNotExist:
                raise BusinessError("Trueque no encontrado.", status_code=404)

            if usuario == trueque.emisor:
                trueque.emisor_confirmado = True
            elif usuario == trueque.receptor:
                trueque.receptor_confirmado = True
            else:
                raise BusinessError("No eres parte de este trueque.", status_code=403)

            self.trueque_repository.guardar(trueque)

            if not (trueque.emisor_confirmado and trueque.receptor_confirmado):
                return "Confirmacion registrada. A la espera de la otra parte."

            emisor = trueque.emisor
            receptor = trueque.receptor

            if emisor.horas_de_vida - 1.0 < -10.0:
                raise BusinessError("Limite de balance negativo excedido (-10).")

            emisor.horas_de_vida -= 1.0
            receptor.horas_de_vida += 1.0
            self.usuario_repository.guardar(emisor)
            self.usuario_repository.guardar(receptor)

            trueque.estado = "FINALIZADO"
            self.trueque_repository.guardar(trueque)
            return "Trueque finalizado. Saldos actualizados. Modal de resena habilitado."


class ResenaService(ResenaInterface):
    def __init__(self, trueque_repository=None, resena_repository=None, usuario_repository=None):
        self.trueque_repository = trueque_repository or AcuerdoTruequeRepository()
        self.resena_repository = resena_repository or ResenaRepository()
        self.usuario_repository = usuario_repository or UsuarioRepository()

    def registrar_resena(self, usuario, datos):
        trueque_id = datos.get("trueque_id")
        comentario = datos.get("comentario", "")

        try:
            estrellas = int(datos.get("estrellas"))
        except (TypeError, ValueError):
            raise BusinessError("Las estrellas deben ser un numero entero.")

        if estrellas < 1 or estrellas > 5:
            raise BusinessError("Las estrellas deben estar entre 1 y 5.")

        try:
            trueque = self.trueque_repository.obtener_bloqueado(trueque_id)
        except ObjectDoesNotExist:
            raise BusinessError("Trueque no encontrado.", status_code=404)

        if usuario not in [trueque.emisor, trueque.receptor]:
            raise BusinessError("No eres parte de este trueque.", status_code=403)

        calificado = trueque.receptor if usuario == trueque.emisor else trueque.emisor
        self.resena_repository.crear(trueque, usuario, calificado, estrellas, comentario)

        resenas = self.resena_repository.listar_por_calificado(calificado)
        total_estrellas = sum(resena.estrellas for resena in resenas)
        calificado.promedio_estrellas = total_estrellas / len(resenas)
        self.usuario_repository.guardar(calificado)

        return "Resena registrada y promedio actualizado."


class ComercioService(ComercioInterface):
    def __init__(self, usuario_repository=None, saldo_repository=None):
        self.usuario_repository = usuario_repository or UsuarioRepository()
        self.saldo_repository = saldo_repository or SaldoComercialRepository()
        self.movimientos = []

    def emitir_vuelto(self, comercio, datos):
        if not comercio.es_comercio:
            raise BusinessError("Solo comercios pueden emitir saldos comerciales.", status_code=403)

        cliente_id = datos.get("cliente_id")
        monto = self._obtener_monto(datos.get("monto_excedente"))

        if not cliente_id:
            raise BusinessError("Faltan datos.")

        with transaction.atomic():
            try:
                cliente = self.usuario_repository.obtener_por_id_bloqueado(cliente_id)
            except ObjectDoesNotExist:
                raise BusinessError("El cliente especificado no existe.", status_code=404)

            cliente.saldo_comercial += monto
            self.usuario_repository.guardar(cliente)
            movimiento = self.saldo_repository.crear_movimiento(comercio, cliente, monto, "EMISION")
            self.movimientos.append(movimiento)

        return "Saldo a favor comercial emitido correctamente (Inalterable en horas de vida)."

    def pagar_con_saldo(self, cliente, datos):
        comercio_id = datos.get("comercio_id")
        monto = self._obtener_monto(datos.get("monto"))

        if not comercio_id:
            raise BusinessError("Faltan datos.")

        with transaction.atomic():
            cliente_bloqueado = self.usuario_repository.obtener_por_id_bloqueado(cliente.id)

            try:
                comercio = self.usuario_repository.obtener_por_id(comercio_id)
            except ObjectDoesNotExist:
                raise BusinessError("Comercio no encontrado.", status_code=404)

            if not comercio.es_comercio:
                raise BusinessError("El usuario de destino no es un comercio.")

            if cliente_bloqueado.saldo_comercial < monto:
                raise BusinessError("Saldo comercial insuficiente para realizar el pago.")

            cliente_bloqueado.saldo_comercial -= monto
            self.usuario_repository.guardar(cliente_bloqueado)
            movimiento = self.saldo_repository.crear_movimiento(comercio, cliente_bloqueado, monto, "PAGO")
            self.movimientos.append(movimiento)

        return "Pago procesado con exito utilizando saldo comercial."

    def listar_comercios(self):
        return self.usuario_repository.listar_comercios_activos()

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


class MatchmakingService(MatchmakingInterface):
    def __init__(self, publicacion_repository=None, matchmaking_repository=None):
        self.publicacion_repository = publicacion_repository or PublicacionRepository()
        self.matchmaking_repository = matchmaking_repository or MatchmakingRepository()
        self.matches = []

    def obtener_matches(self, usuario):
        mis_necesidades = self.publicacion_repository.categorias_activas_por_usuario_y_tipo(usuario, "NECESIDAD")
        mis_talentos = self.publicacion_repository.categorias_activas_por_usuario_y_tipo(usuario, "TALENTO")
        self.matches = self.matchmaking_repository.buscar_matches(usuario, mis_necesidades, mis_talentos)
        return self.matches

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
    NotificacionPropuestaRepository,
    PublicacionRepository,
    ResenaRepository,
    SaldoComercialRepository,
    UsuarioAutorizadoRepository,
    UsuarioRepository,
)
from .validators import contiene_palabra_prohibida

CATEGORIAS_PUBLICACION = {
    "Mantenimiento, Reparaciones y Construcción",
    "Tecnología, Desarrollo y Redes",
    "Limpieza, Organización y Hogar",
    "Diseño, Multimedia y Arte",
    "Redacción, Traducción y Contenidos",
    "Educación, Asesoría y Tutorías",
    "Automotriz, Transporte y Logística",
    "Eventos, Ocio y Entretenimiento",
    "Cuidado de la Salud, Bienestar y Terapias",
}


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
        
        # Intentar formato nuevo con secciones separadas
        try:
            return self._cargar_formato_secciones(data)
        except BusinessError:
            # Si falla, intentar formato antiguo con columnas
            return self._cargar_formato_columnas(data)

    def _cargar_formato_secciones(self, data):
        creados = 0
        self.emails_procesados = []
        seccion_actual = None
        
        for linea in data:
            linea = linea.strip()
            if not linea:
                continue
            
            if linea == "email Usuarios":
                seccion_actual = "USUARIO"
                continue
            elif linea == "email Comercios":
                seccion_actual = "COMERCIO"
                continue
            
            if seccion_actual and linea:
                email = linea
                _, creado = self.autorizados_repository.guardar_email(email, seccion_actual)
                self.emails_procesados.append(f"{email} ({seccion_actual.lower()})")
                if creado:
                    creados += 1
        
        if not self.emails_procesados:
            raise BusinessError("No se encontraron emails en el archivo.")
        
        return {
            "mensaje": f"Lista procesada con exito. Se cargaron {creados} correos autorizados.",
            "emails_procesados": self.emails_procesados,
        }

    def _cargar_formato_columnas(self, data):
        reader = csv.DictReader(data)
        if not reader.fieldnames:
            raise BusinessError("El CSV debe tener las columnas 'email Usuarios' y 'email Comercios'.")

        creados = 0
        self.emails_procesados = []
        for row in reader:
            for columna, tipo in (("email Usuarios", "USUARIO"), ("email Comercios", "COMERCIO")):
                email = (row.get(columna) or "").strip()
                if not email:
                    continue

                _, creado = self.autorizados_repository.guardar_email(email, tipo)
                self.emails_procesados.append(f"{email} ({tipo.lower()})")
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

    def validar_email(self, datos):
        email = datos.get("email")
        es_comercio = bool(datos.get("es_comercio", False))
        tipo_autorizado = "COMERCIO" if es_comercio else "USUARIO"

        if not email:
            raise BusinessError("Faltan datos obligatorios.")

        if not self.autorizados_repository.existe_email(email, tipo_autorizado):
            mensaje = "Comercio no autorizado para esta comunidad." if es_comercio else "Usuario no autorizado para esta comunidad."
            raise BusinessError(mensaje, status_code=403)

        return True

    def registrar_usuario(self, datos):
        email = datos.get("email")
        username = datos.get("username")
        password = datos.get("password")
        nombre_real = datos.get("nombre_real")
        es_comercio = bool(datos.get("es_comercio", False))

        if not all([email, username, password, nombre_real]):
            raise BusinessError("Faltan datos obligatorios.")

        self.validar_email({"email": email, "es_comercio": es_comercio})

        if self.usuario_repository.existe_username(username):
            raise BusinessError("El username ya esta en uso.")

        return self.usuario_repository.crear_usuario(username, email, password, nombre_real, es_comercio)


class PublicacionService:
    def __init__(self, publicacion_repository=None, matchmaking_service=None):
        self.publicacion_repository = publicacion_repository or PublicacionRepository()
        self.matchmaking_service = matchmaking_service

    def _disparar_deteccion_matches(self, usuario):
        servicio = self.matchmaking_service or MatchmakingService()
        servicio.detectar_y_notificar_matches(usuario)

    def crear_publicacion(self, usuario, datos):
        tipo = datos.get("tipo")
        titulo = datos.get("titulo")
        descripcion = datos.get("descripcion")
        categoria = datos.get("categoria")
        urgencia = datos.get("urgencia", "NORMAL")

        if not all([tipo, titulo, descripcion, categoria]):
            raise BusinessError("Faltan datos obligatorios para la publicacion.")

        if tipo not in ["TALENTO", "NECESIDAD"]:
            raise BusinessError("El tipo debe ser TALENTO o NECESIDAD.")

        if categoria not in CATEGORIAS_PUBLICACION:
            raise BusinessError("La categoria seleccionada no esta permitida.")

        if urgencia not in ["NORMAL", "ALTA", "CRITICA"]:
            raise BusinessError("La urgencia seleccionada no es valida.")

        # Usar método de negocio de Usuario para verificar si puede publicar
        puede_publicar, mensaje = usuario.puede_publicar(tipo)
        if not puede_publicar:
            raise BusinessError(mensaje)

        if contiene_palabra_prohibida(titulo) or contiene_palabra_prohibida(descripcion):
            raise BusinessError("La publicación contiene palabras no permitidas.")

        # Crear publicación temporal para validar reglas de negocio
        from .models import Publicacion
        publicacion_temp = Publicacion(
            usuario=usuario,
            tipo=tipo,
            titulo=titulo,
            descripcion=descripcion,
            categoria=categoria,
            urgencia=urgencia,
            esta_activa=True
        )
        
        # Usar método de negocio de Publicacion para validar reglas
        es_valido, mensaje_validacion = publicacion_temp.validar_reglas_negocio()
        if not es_valido:
            raise BusinessError(mensaje_validacion)

        publicacion = self.publicacion_repository.crear(usuario, {
            "tipo": tipo,
            "titulo": titulo,
            "descripcion": descripcion,
            "categoria": categoria,
            "urgencia": urgencia,
        })
        self._disparar_deteccion_matches(usuario)
        return publicacion

    def pausar_publicacion(self, usuario, publicacion_id):
        return self.actualizar_estado_publicacion(usuario, publicacion_id, esta_activa=False)

    def reactivar_publicacion(self, usuario, publicacion_id):
        return self.actualizar_estado_publicacion(usuario, publicacion_id, esta_activa=True)

    def actualizar_estado_publicacion(self, usuario, publicacion_id, esta_activa):
        from .models import Publicacion

        # Usar método de negocio de Usuario para verificar si puede modificar publicaciones
        if not usuario.puede_modificar_publicaciones():
            raise BusinessError("Saldo crítico inferior a -10 horas. No puedes modificar ofertas.")

        try:
            publicacion = self.publicacion_repository.obtener_por_id_y_usuario(publicacion_id, usuario)
        except Publicacion.DoesNotExist:
            raise BusinessError("Publicación no encontrada.", status_code=404)

        # Usar métodos de negocio de Publicacion para validar
        if esta_activa and not publicacion.esta_activa:
            puede_reactivar, mensaje = publicacion.puede_reactivarse()
            if not puede_reactivar:
                raise BusinessError(mensaje)
        elif not esta_activa and publicacion.esta_activa:
            puede_pausar, mensaje = publicacion.puede_pausarse()
            if not puede_pausar:
                raise BusinessError(mensaje)

        publicacion.esta_activa = esta_activa
        publicacion.save(update_fields=["esta_activa"])
        if esta_activa:
            self._disparar_deteccion_matches(usuario)
        return publicacion


class CarteleraService(CarteleraInterface):
    def __init__(self, publicacion_repository=None):
        self.publicacion_repository = publicacion_repository or PublicacionRepository()

    def obtener_publicaciones(self, categoria=None, urgencias=None):
        return self.publicacion_repository.obtener_cartelera(categoria=categoria, urgencias=urgencias)


class TruequeService(TruequeInterface):
    def __init__(self, trueque_repository=None, usuario_repository=None, publicacion_repository=None, notificacion_service=None):
        self.trueque_repository = trueque_repository or AcuerdoTruequeRepository()
        self.usuario_repository = usuario_repository or UsuarioRepository()
        self.publicacion_repository = publicacion_repository or PublicacionRepository()
        self.notificacion_service = notificacion_service or NotificacionService()

    @staticmethod
    def _es_intercambio_mutuo(trueque):
        """Trueque complementario: ambas partes ofrecen un TALENTO (impacto 0 horas)."""
        # Usar método de negocio de AcuerdoTrueque para verificar si es intercambio mutuo
        return trueque.es_intercambio_mutuo()

    @staticmethod
    def _identificar_roles_trueque(trueque):
        """Determina prestador (TALENTO) y receptor_servicio (NECESIDAD) según publicaciones."""
        prestador = None
        receptor_servicio = None

        for usuario, publicacion in (
            (trueque.emisor, trueque.publicacion_emisor),
            (trueque.receptor, trueque.publicacion_receptor),
        ):
            if not publicacion:
                continue
            # Usar métodos de negocio de Publicacion
            if publicacion.es_talento():
                prestador = usuario
            elif publicacion.es_necesidad():
                receptor_servicio = usuario

        if prestador and receptor_servicio:
            return prestador, receptor_servicio

        # Fallback sin publicaciones: emisor pierde hora, receptor gana hora.
        return trueque.receptor, trueque.emisor

    @staticmethod
    def _validar_publicaciones_propuesta(emisor, receptor, pub_emisor, pub_receptor):
        if pub_emisor and pub_emisor.usuario_id != emisor.id:
            raise BusinessError("La publicación del emisor no pertenece al usuario emisor.")
        if pub_receptor and pub_receptor.usuario_id != receptor.id:
            raise BusinessError("La publicación del receptor no pertenece al usuario receptor.")

        if not pub_emisor or not pub_receptor:
            return

        if pub_emisor.id == pub_receptor.id:
            raise BusinessError("No se puede usar la misma publicación en ambos lados del trueque.")

        # Usar métodos de negocio de Publicacion para validar tipos
        tipo_emisor = "TALENTO" if pub_emisor.es_talento() else "NECESIDAD"
        tipo_receptor = "TALENTO" if pub_receptor.es_talento() else "NECESIDAD"

        if pub_emisor.es_necesidad() and pub_receptor.es_necesidad():
            raise BusinessError(
                "No se puede proponer un trueque entre dos necesidades. Una necesidad debe cubrirse "
                "con un talento ofrecido."
            )

        combinaciones_validas = {
            ("TALENTO", "NECESIDAD"),
            ("NECESIDAD", "TALENTO"),
            ("TALENTO", "TALENTO"),
        }
        if (tipo_emisor, tipo_receptor) not in combinaciones_validas:
            raise BusinessError("Combinación de publicaciones no válida para un trueque.")

    @staticmethod
    def _mensaje_propuesta(emisor, pub_emisor, pub_receptor):
        nombre = emisor.nombre_real
        if pub_emisor.es_talento() and pub_receptor.es_necesidad():
            return (
                f"{nombre} te ofrece {pub_emisor.titulo} "
                f"para tu necesidad de {pub_receptor.titulo}."
            )
        if pub_emisor.es_necesidad() and pub_receptor.es_talento():
            return (
                f"{nombre} solicita tu talento en {pub_receptor.titulo} "
                f"(necesita {pub_emisor.titulo})."
            )
        return (
            f"{nombre} te propone intercambio mutuo: "
            f"ofrece {pub_emisor.titulo} a cambio de {pub_receptor.titulo}."
        )

    def crear_propuesta(self, emisor, receptor_id, publicacion_emisor_id=None, publicacion_receptor_id=None):
        """Crea una propuesta de trueque con referencias a las publicaciones específicas."""
        if not receptor_id:
            raise BusinessError("Falta receptor_id.")

        try:
            receptor = self.usuario_repository.obtener_por_id(receptor_id)
        except ObjectDoesNotExist:
            raise BusinessError("Receptor no encontrado.", status_code=404)

        if receptor.id == emisor.id:
            raise BusinessError("No puedes enviarte una propuesta a ti mismo.")

        # Obtener las publicaciones si se proporcionan
        from .models import Publicacion
        pub_emisor = None
        pub_receptor = None
        
        if publicacion_emisor_id:
            try:
                pub_emisor = Publicacion.objects.get(id=publicacion_emisor_id, esta_activa=True)
            except Publicacion.DoesNotExist:
                raise BusinessError("Publicación del emisor no encontrada.", status_code=404)
        
        if publicacion_receptor_id:
            try:
                pub_receptor = Publicacion.objects.get(id=publicacion_receptor_id, esta_activa=True)
            except Publicacion.DoesNotExist:
                raise BusinessError("Publicación del receptor no encontrada.", status_code=404)

        self._validar_publicaciones_propuesta(emisor, receptor, pub_emisor, pub_receptor)

        trueque = self.trueque_repository.obtener_o_crear_pendiente(
            emisor=emisor,
            receptor=receptor,
            publicacion_emisor=pub_emisor,
            publicacion_receptor=pub_receptor,
        )

        if pub_receptor and pub_emisor:
            mensaje = self._mensaje_propuesta(emisor, pub_emisor, pub_receptor)
            self.notificacion_service.crear_notificacion_propuesta(
                destinatario=receptor,
                remitente=emisor,
                trueque=trueque,
                publicacion_original=pub_receptor,
                mensaje=mensaje,
                tipo="PROPUESTA",
            )

        return trueque

    def responder_propuesta(self, receptor, trueque_id, accion):
        try:
            trueque = self.trueque_repository.obtener_por_receptor(trueque_id, receptor)
        except ObjectDoesNotExist:
            raise BusinessError("Propuesta no encontrada.", status_code=404)

        if accion == "ACEPTAR":
            trueque.estado = "ACEPTADO"
            self.trueque_repository.guardar(trueque)
            self.notificacion_service.actualizar_estado_propuesta(trueque, "ACEPTADA")
            return "Propuesta aceptada. Confirma la finalización cuando el servicio esté completo."

        if accion == "RECHAZAR":
            trueque.estado = "RECHAZADO"
            self.trueque_repository.guardar(trueque)
            self.notificacion_service.actualizar_estado_propuesta(trueque, "RECHAZADA")
            return "Propuesta rechazada."

        raise BusinessError("Accion invalida.")

    def finalizar_trueque(self, usuario, trueque_id):
        """Confirmación bilateral antes de transferir el saldo de horas."""
        with transaction.atomic():
            try:
                trueque = self.trueque_repository.obtener_bloqueado(trueque_id)
            except ObjectDoesNotExist:
                raise BusinessError("Trueque no encontrado.", status_code=404)

            # Usar método de negocio de AcuerdoTrueque para verificar participación
            if not trueque.participante(usuario):
                raise BusinessError("No eres parte de este trueque.", status_code=403)

            if not trueque.esta_aceptado():
                raise BusinessError("El trueque debe estar aceptado para confirmar finalización.", status_code=400)

            # Usar método de negocio de AcuerdoTrueque para verificar si puede confirmar
            puede_confirmar, mensaje = trueque.puede_confirmar(usuario)
            if not puede_confirmar:
                raise BusinessError(mensaje)

            if usuario == trueque.emisor:
                trueque.emisor_confirmado = True
            else:
                trueque.receptor_confirmado = True

            # Usar método de negocio de AcuerdoTrueque para verificar si ambas partes confirmaron
            if not trueque.ambas_partes_confirmaron():
                self.trueque_repository.guardar(trueque)
                return {
                    "saldo_transferido": False,
                    "impacto_horas": 0,
                    "habilitar_resena": False,
                    "mensaje": "Confirmación registrada. Esperando confirmación de la otra parte.",
                }

            # Usar método de negocio de AcuerdoTrueque para verificar si es intercambio mutuo
            if trueque.es_intercambio_mutuo():
                trueque.estado = "FINALIZADO"
                self.trueque_repository.guardar(trueque)
                return {
                    "saldo_transferido": False,
                    "impacto_horas": 0,
                    "habilitar_resena": True,
                    "mensaje": (
                        "Trueque mutuo finalizado. Intercambio equilibrado sin transferencia "
                        "de horas. Sistema de reseñas habilitado."
                    ),
                }

            prestador, receptor_servicio = self._identificar_roles_trueque(trueque)

            prestador = self.usuario_repository.obtener_por_id_bloqueado(prestador.id)
            receptor_servicio = self.usuario_repository.obtener_por_id_bloqueado(receptor_servicio.id)

            # Usar método de negocio de Usuario para verificar límite de saldo
            if receptor_servicio.horas_de_vida - 1.0 < -10.0:
                raise BusinessError(
                    "El usuario que recibe el servicio excedería el límite de -10 horas.",
                )

            prestador.horas_de_vida += 1.0
            receptor_servicio.horas_de_vida -= 1.0
            self.usuario_repository.guardar(prestador)
            self.usuario_repository.guardar(receptor_servicio)

            trueque.estado = "FINALIZADO"
            self.trueque_repository.guardar(trueque)
            return {
                "saldo_transferido": True,
                "impacto_horas": 1,
                "habilitar_resena": True,
                "mensaje": "Trueque finalizado. Saldos actualizados. Sistema de reseñas habilitado.",
            }


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

        if len(comentario) > 500:
            raise BusinessError("El comentario no puede superar los 500 caracteres.")

        with transaction.atomic():
            try:
                trueque = self.trueque_repository.obtener_bloqueado(trueque_id)
            except ObjectDoesNotExist:
                raise BusinessError("Trueque no encontrado.", status_code=404)

            # Usar método de negocio de AcuerdoTrueque para verificar participación
            if not trueque.participante(usuario):
                raise BusinessError("No eres parte de este trueque.", status_code=403)

            if not trueque.esta_finalizado():
                raise BusinessError("Solo se pueden dejar reseñas de trueques finalizados.", status_code=400)

            # Verificar si ya existe una reseña de este usuario para este trueque
            try:
                from .models import Resena
                Resena.objects.get(trueque=trueque, calificador=usuario)
                raise BusinessError("Ya has dejado una reseña para este trueque.", status_code=400)
            except Resena.DoesNotExist:
                pass  # No hay reseña previa, podemos continuar

            calificado = trueque.contraparte(usuario)
            
            # Crear reseña temporal para validar usando métodos de negocio
            resena_temp = Resena(
                trueque=trueque,
                calificador=usuario,
                calificado=calificado,
                estrellas=estrellas,
                comentario=comentario
            )
            
            # Usar método de negocio de Resena para validar
            es_valida, mensaje = resena_temp.validar_resena()
            if not es_valida:
                raise BusinessError(mensaje)

            self.resena_repository.crear(trueque, usuario, calificado, estrellas, comentario)

        return "Resena registrada correctamente."


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

        if not cliente_id:
            raise BusinessError("Faltan datos.")

        # Usar método de negocio de Usuario para validar saldo comercial
        puede_emitir, mensaje = comercio.puede_emitir_vuelto_comercial(monto)
        if not puede_emitir:
            raise BusinessError(mensaje, status_code=403)

        with transaction.atomic():
            try:
                cliente = self.usuario_repository.obtener_por_id_bloqueado(cliente_id)
            except ObjectDoesNotExist:
                raise BusinessError("El cliente especificado no existe.", status_code=404)

            cliente.saldo_comercial += monto
            comercio.saldo_comercial -= monto
            self.usuario_repository.guardar(cliente)
            self.usuario_repository.guardar(comercio)
            movimiento = self.saldo_repository.crear_movimiento(comercio, cliente, monto, "EMISION")
            self.movimientos.append(movimiento)

        return "Saldo a favor comercial emitido correctamente (Inalterable en horas de vida)."

    def pagar_con_saldo(self, cliente, datos):
        comercio_id = datos.get("comercio_id")
        monto = self._obtener_monto(datos.get("monto"))

        if not comercio_id:
            raise BusinessError("Faltan datos.")

        # Usar método de negocio de Usuario para validar saldo comercial
        puede_pagar, mensaje = cliente.puede_pagar_con_saldo(monto)
        if not puede_pagar:
            raise BusinessError(mensaje)

        with transaction.atomic():
            cliente_bloqueado = self.usuario_repository.obtener_por_id_bloqueado(cliente.id)

            try:
                comercio = self.usuario_repository.obtener_por_id(comercio_id)
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

        return "Pago procesado con exito utilizando saldo comercial."

    def listar_comercios(self):
        comercios = self.usuario_repository.listar_comercios_activos()
        # Filtrar usando método de negocio de Usuario para asegurar que sean comercios activos
        return [c for c in comercios if c.es_comercio_activo()]

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


class NotificacionService:
    def __init__(self, notificacion_repository=None):
        self.notificacion_repository = notificacion_repository or NotificacionPropuestaRepository()

    def crear_notificacion_propuesta(
        self,
        destinatario,
        remitente,
        trueque,
        publicacion_original,
        mensaje,
        tipo="PROPUESTA",
    ):
        return self.notificacion_repository.crear_notificacion(
            destinatario,
            remitente,
            trueque,
            publicacion_original,
            mensaje,
            tipo=tipo,
        )

    def actualizar_estado_propuesta(self, trueque, estado):
        return self.notificacion_repository.actualizar_estado_por_trueque(trueque, estado)
    
    def obtener_notificaciones_usuario(self, usuario, incluir_leidas=False):
        return self.notificacion_repository.obtener_notificaciones_usuario(
            usuario,
            incluir_leidas=incluir_leidas,
        )
    
    def marcar_notificacion_leida(self, notificacion_id, usuario):
        try:
            return self.notificacion_repository.marcar_como_leida(
                notificacion_id,
                destinatario=usuario,
            )
        except ObjectDoesNotExist:
            raise BusinessError("Notificación no encontrada.", status_code=404)

    def marcar_notificaciones_trueque_leidas(self, usuario, trueque_id):
        actualizadas = self.notificacion_repository.marcar_leidas_por_trueque(
            usuario,
            trueque_id,
        )
        return actualizadas


class MatchmakingService(MatchmakingInterface):
    def __init__(
        self,
        publicacion_repository=None,
        matchmaking_repository=None,
        notificacion_repository=None,
        trueque_repository=None,
    ):
        self.publicacion_repository = publicacion_repository or PublicacionRepository()
        self.matchmaking_repository = matchmaking_repository or MatchmakingRepository()
        self.notificacion_repository = notificacion_repository or NotificacionPropuestaRepository()
        self.trueque_repository = trueque_repository or AcuerdoTruequeRepository()
        self.matches = []

    def obtener_matches(self, usuario):
        titulos_necesidades = self.publicacion_repository.titulos_activos_por_usuario_y_tipo(
            usuario, "NECESIDAD"
        )
        titulos_talentos = self.publicacion_repository.titulos_activos_por_usuario_y_tipo(
            usuario, "TALENTO"
        )
        self.matches = self.matchmaking_repository.buscar_matches(
            usuario, titulos_necesidades, titulos_talentos
        )
        return self.matches

    def verificar_coincidencia_por_titulo(self, usuario, publicacion_id):
        """Verifica si el usuario tiene publicaciones con el mismo título que la publicación seleccionada."""
        try:
            from .models import Publicacion
            publicacion = Publicacion.objects.get(id=publicacion_id, esta_activa=True)
            resultado = self.matchmaking_repository.verificar_coincidencia_por_titulo(usuario, publicacion)
            return resultado
        except Publicacion.DoesNotExist:
            return {
                "tiene_coincidencia": False,
                "publicaciones_coincidentes": [],
                "tipo_buscado": None,
                "titulo": None,
                "error": "Publicación no encontrada"
            }
    
    def obtener_matches_por_publicacion(self, usuario, publicacion_id):
        """Obtiene matches basados en una publicación específica."""
        try:
            from .models import Publicacion
            publicacion = Publicacion.objects.get(id=publicacion_id, esta_activa=True)
            self.matches = self.matchmaking_repository.buscar_matches_por_publicacion(usuario, publicacion)
            return self.matches
        except Publicacion.DoesNotExist:
            return []

    @staticmethod
    def _construir_match_detalle(match, usuario):
        """Arma las dos parejas del match desde la perspectiva del destinatario."""
        from .models import Publicacion

        detalle = []
        vistos = set()

        for sugerencia in match.get("publicaciones_sugeridas", []):
            mi_pub = Publicacion.objects.filter(id=sugerencia.get("mi_pub_id")).first()
            su_pub = Publicacion.objects.filter(id=sugerencia.get("su_pub_id")).first()
            if not mi_pub or not su_pub or mi_pub.usuario_id != usuario.id:
                continue
            if mi_pub.tipo == "NECESIDAD" and su_pub.tipo == "TALENTO":
                rol = "recibo"
            elif mi_pub.tipo == "TALENTO" and su_pub.tipo == "NECESIDAD":
                rol = "doy"
            else:
                continue
            clave = (rol, mi_pub.titulo)
            if clave in vistos:
                continue
            vistos.add(clave)
            detalle.append(
                {
                    "rol": rol,
                    "mi_titulo": mi_pub.titulo,
                    "mi_tipo": mi_pub.tipo,
                    "su_titulo": su_pub.titulo,
                    "su_tipo": su_pub.tipo,
                }
            )

        if len(detalle) < 2:
            otro_usuario = match["usuario"]
            for tal_otro in match.get("talentos_coincidentes", []):
                mi_nec = Publicacion.objects.filter(
                    usuario=usuario,
                    tipo="NECESIDAD",
                    titulo=tal_otro.titulo,
                    esta_activa=True,
                ).first()
                if not mi_nec:
                    continue
                clave = ("recibo", mi_nec.titulo)
                if clave in vistos:
                    continue
                vistos.add(clave)
                detalle.append(
                    {
                        "rol": "recibo",
                        "mi_titulo": mi_nec.titulo,
                        "mi_tipo": "NECESIDAD",
                        "su_titulo": tal_otro.titulo,
                        "su_tipo": "TALENTO",
                    }
                )

            for nec_otro in match.get("necesidades_coincidentes", []):
                mi_tal = Publicacion.objects.filter(
                    usuario=usuario,
                    tipo="TALENTO",
                    titulo=nec_otro.titulo,
                    esta_activa=True,
                ).first()
                if not mi_tal:
                    continue
                clave = ("doy", mi_tal.titulo)
                if clave in vistos:
                    continue
                vistos.add(clave)
                detalle.append(
                    {
                        "rol": "doy",
                        "mi_titulo": mi_tal.titulo,
                        "mi_tipo": "TALENTO",
                        "su_titulo": nec_otro.titulo,
                        "su_tipo": "NECESIDAD",
                    }
                )

        orden = {"recibo": 0, "doy": 1}
        detalle.sort(key=lambda entrada: orden.get(entrada["rol"], 2))
        return detalle

    @staticmethod
    def _mensaje_match_desde_detalle(match_detalle, otro_nombre, es_mutuo, match):
        recibo = next((entrada for entrada in match_detalle if entrada["rol"] == "recibo"), None)
        doy = next((entrada for entrada in match_detalle if entrada["rol"] == "doy"), None)

        if es_mutuo and recibo and doy:
            return (
                f"¡Match con {otro_nombre}! Tú necesitas {recibo['mi_titulo']} (ellos ofrecen) "
                f"y ofreces {doy['mi_titulo']} (ellos necesitan)."
            )

        talento_titulo = (
            match["talentos_coincidentes"][0].titulo if match.get("talentos_coincidentes") else "un servicio"
        )
        necesidad_titulo = (
            match["necesidades_coincidentes"][0].titulo
            if match.get("necesidades_coincidentes")
            else "otro servicio"
        )
        if es_mutuo:
            return (
                f"¡Match complementario! Intercambio equilibrado con {otro_nombre}: "
                f"tú ofreces {doy['mi_titulo'] if doy else talento_titulo}, "
                f"recibes {recibo['mi_titulo'] if recibo else necesidad_titulo} (0 horas netas)."
            )
        return (
            f"¡Match! {otro_nombre} ofrece {talento_titulo} "
            f"y necesita {necesidad_titulo}. Coincide con tu perfil."
        )

    @staticmethod
    def _resolver_publicaciones_match_completo(match, usuario):
        """Match complementario: talento propio + talento del vecino (0 horas netas)."""
        from .models import Publicacion

        if not match.get("talentos_coincidentes") or not match.get("necesidades_coincidentes"):
            return None, None

        titulos_que_yo_ofrezco = [nec.titulo for nec in match["necesidades_coincidentes"]]
        pub_usuario = Publicacion.objects.filter(
            usuario=usuario,
            tipo="TALENTO",
            esta_activa=True,
            titulo__in=titulos_que_yo_ofrezco,
        ).first()
        pub_otro = match["talentos_coincidentes"][0]

        if pub_usuario and pub_otro:
            return pub_usuario, pub_otro
        return None, None

    def detectar_y_notificar_matches(self, usuario):
        matches = self.obtener_matches(usuario)
        notificaciones_creadas = []

        for match in matches:
            otro_usuario = match["usuario"]
            if self.notificacion_repository.existe_match_entre(usuario, otro_usuario):
                continue

            pub_emisor, pub_receptor = self._resolver_publicaciones_match_completo(match, usuario)

            if not pub_emisor:
                sugerencia = match["publicaciones_sugeridas"][0] if match["publicaciones_sugeridas"] else {}
                if sugerencia:
                    from .models import Publicacion

                    pub_emisor = Publicacion.objects.filter(id=sugerencia.get("mi_pub_id")).first()
                    pub_receptor = Publicacion.objects.filter(id=sugerencia.get("su_pub_id")).first()

            trueque = self.trueque_repository.obtener_o_crear_pendiente(
                emisor=usuario,
                receptor=otro_usuario,
                publicacion_emisor=pub_emisor,
                publicacion_receptor=pub_receptor,
            )

            es_mutuo = TruequeService._es_intercambio_mutuo(trueque)
            publicacion_referencia = pub_receptor or pub_emisor

            if not publicacion_referencia:
                continue

            match_detalle_usuario = self._construir_match_detalle(match, usuario)
            mensaje_para_usuario = self._mensaje_match_desde_detalle(
                match_detalle_usuario,
                otro_usuario.nombre_real,
                es_mutuo,
                match,
            )
            notificaciones_creadas.append(
                self.notificacion_repository.crear_notificacion(
                    destinatario=usuario,
                    remitente=otro_usuario,
                    trueque=trueque,
                    publicacion_original=publicacion_referencia,
                    mensaje=mensaje_para_usuario,
                    tipo="MATCH",
                    match_detalle=match_detalle_usuario or None,
                )
            )

            match_detalle_otro = self._construir_match_detalle(match, otro_usuario)
            mensaje_para_match = self._mensaje_match_desde_detalle(
                match_detalle_otro,
                usuario.nombre_real,
                es_mutuo,
                match,
            )
            notificaciones_creadas.append(
                self.notificacion_repository.crear_notificacion(
                    destinatario=otro_usuario,
                    remitente=usuario,
                    trueque=trueque,
                    publicacion_original=publicacion_referencia,
                    mensaje=mensaje_para_match,
                    tipo="MATCH",
                    match_detalle=match_detalle_otro or None,
                )
            )

        return notificaciones_creadas

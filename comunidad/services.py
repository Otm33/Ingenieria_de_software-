import csv
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q

from .interfaces import (
    CarteleraInterface,
    CargaUsuariosInterface,
    ComercioInterface,
    MatchmakingInterface,
    RegistroUsuariosInterface,
    ResenaInterface,
    TruequeInterface,
)
from .models import (
    AcuerdoTrueque,
    DonacionHoras,
    NotificacionPropuesta,
    Publicacion,
    Resena,
    SaldoComercial,
    SolicitudApoyoSocial,
    Usuario,
    UsuarioAutorizado,
)
from .catalogo_causas_sociales import (
    categoria_para_titulo,
    es_categoria_causa_social_permitida,
    es_titulo_causa_social_permitido,
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


def _validar_usuario_no_comercio_trueques(usuario):
    if usuario.es_comercio:
        raise BusinessError(
            "Los comercios no participan del mercado de trueques.",
            status_code=403,
        )


class CargaUsuariosService(CargaUsuariosInterface):
    def __init__(self):
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
                _, creado = UsuarioAutorizado.objects.guardar_email(email, seccion_actual)
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

                _, creado = UsuarioAutorizado.objects.guardar_email(email, tipo)
                self.emails_procesados.append(f"{email} ({tipo.lower()})")
                if creado:
                    creados += 1

        return {
            "mensaje": f"Lista procesada con exito. Se cargaron {creados} correos autorizados.",
            "emails_procesados": self.emails_procesados,
        }


class RegistroUsuarioService(RegistroUsuariosInterface):
    def validar_email(self, datos):
        email = datos.get("email")
        es_comercio = bool(datos.get("es_comercio", False))
        tipo_autorizado = "COMERCIO" if es_comercio else "USUARIO"

        if not email:
            raise BusinessError("Faltan datos obligatorios.")

        if not UsuarioAutorizado.objects.existe_email(email, tipo_autorizado):
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

        if Usuario.objects.existe_username(username):
            raise BusinessError("El username ya esta en uso.")

        return Usuario.objects.crear_usuario(username, email, password, nombre_real, es_comercio)


class PublicacionService:
    def __init__(self, matchmaking_service=None):
        self.matchmaking_service = matchmaking_service

    def _disparar_deteccion_matches(self, usuario):
        servicio = self.matchmaking_service or MatchmakingService()
        servicio.detectar_y_notificar_matches(usuario)

    def crear_publicacion(self, usuario, datos):
        if usuario.es_comercio:
            raise BusinessError(
                "Los comercios no pueden publicar talentos ni necesidades.",
                status_code=403,
            )

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

        if tipo == "TALENTO" and urgencia != "NORMAL":
            raise BusinessError("Los talentos solo pueden tener urgencia Normal.")

        if contiene_palabra_prohibida(titulo) or contiene_palabra_prohibida(descripcion):
            raise BusinessError("La publicación contiene palabras no permitidas.")

        publicacion = Publicacion.objects.crear(usuario, {
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

        if usuario.horas_de_vida < -10:
            raise BusinessError("Saldo crítico inferior a -10 horas. No puedes modificar ofertas.")

        try:
            publicacion = Publicacion.objects.obtener_por_id_y_usuario(publicacion_id, usuario)
        except Publicacion.DoesNotExist:
            raise BusinessError("Publicación no encontrada.", status_code=404)

        # Solo validar limites cuando se re-activan publicaciones
        if esta_activa and not publicacion.esta_activa:
            if publicacion.tipo == "TALENTO":
                conteo_activas = Publicacion.objects.contar_activas_por_tipo(usuario, publicacion.tipo)
                if conteo_activas >= 5:
                    raise BusinessError("No puedes tener más de 5 talentos activos publicados simultáneamente.")
            elif publicacion.tipo == "NECESIDAD" and not publicacion.es_causa_social:
                conteo_activas = Publicacion.objects.filter(
                    usuario=usuario,
                    tipo="NECESIDAD",
                    esta_activa=True,
                    es_causa_social=False,
                ).count()
                if conteo_activas >= 3:
                    raise BusinessError("No puedes tener más de 3 necesidades activas simultáneamente.")

        publicacion.esta_activa = esta_activa
        publicacion.save(update_fields=["esta_activa"])
        if esta_activa:
            self._disparar_deteccion_matches(usuario)
        return publicacion


class CarteleraService(CarteleraInterface):
    def obtener_publicaciones(self, categoria=None, urgencias=None):
        return Publicacion.objects.obtener_cartelera(categoria=categoria, urgencias=urgencias)


class TruequeService(TruequeInterface):
    def __init__(self, notificacion_service=None):
        self.notificacion_service = notificacion_service or NotificacionService()

    @staticmethod
    def _obtener_solicitud_social_desde_publicacion(publicacion):
        if not publicacion:
            return None
        try:
            return publicacion.solicitud_apoyo_social
        except SolicitudApoyoSocial.DoesNotExist:
            return None

    @staticmethod
    def _resolver_solicitud_social_pago(receptor_servicio, publicacion_necesidad):
        if not publicacion_necesidad or publicacion_necesidad.tipo != "NECESIDAD":
            return None
        if publicacion_necesidad.usuario_id != receptor_servicio.id:
            return None

        solicitud = TruequeService._obtener_solicitud_social_desde_publicacion(publicacion_necesidad)
        if solicitud:
            return solicitud

        return SolicitudApoyoSocial.objects.filter(
            solicitante=receptor_servicio,
            estado="APROBADA",
            titulo=publicacion_necesidad.titulo,
        ).first()

    @staticmethod
    def _descontar_pago_trueque(receptor_servicio, publicacion_necesidad, monto=1.0):
        solicitud = TruequeService._resolver_solicitud_social_pago(
            receptor_servicio,
            publicacion_necesidad,
        )
        if solicitud:
            solicitud = SolicitudApoyoSocial.objects.select_for_update().get(id=solicitud.id)
            if solicitud.horas_solidarias_disponibles < monto:
                raise BusinessError(
                    "No tienes horas solidarias suficientes para esta causa. "
                    "Las donaciones solidarias deben usarse en la necesidad vinculada a tu solicitud aprobada.",
                )
            solicitud.horas_solidarias_disponibles -= monto
            solicitud.horas_solidarias_utilizadas += monto
            solicitud.save(update_fields=["horas_solidarias_disponibles", "horas_solidarias_utilizadas"])
            return "solidarias"

        if receptor_servicio.horas_de_vida - monto < -10.0:
            raise BusinessError("El usuario que recibe el servicio excedería el límite de -10 horas.")
        receptor_servicio.horas_de_vida -= monto
        return "general"

    @staticmethod
    def _obtener_publicacion_necesidad_trueque(trueque, receptor_servicio):
        for usuario, publicacion in (
            (trueque.emisor, trueque.publicacion_emisor),
            (trueque.receptor, trueque.publicacion_receptor),
        ):
            if (
                publicacion
                and publicacion.tipo == "NECESIDAD"
                and usuario.id == receptor_servicio.id
            ):
                return publicacion
        return None

    @staticmethod
    def _es_intercambio_mutuo(trueque):
        """Trueque complementario: ambas partes ofrecen un TALENTO (impacto 0 horas)."""
        pe = trueque.publicacion_emisor
        pr = trueque.publicacion_receptor
        if not pe or not pr:
            return False
        if pe.tipo != "TALENTO" or pr.tipo != "TALENTO":
            return False
        participantes = {trueque.emisor_id, trueque.receptor_id}
        return participantes == {pe.usuario_id, pr.usuario_id}

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
            if publicacion.tipo == "TALENTO":
                prestador = usuario
            elif publicacion.tipo == "NECESIDAD":
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

        tipo_emisor = pub_emisor.tipo
        tipo_receptor = pub_receptor.tipo

        if tipo_emisor == "NECESIDAD" and tipo_receptor == "NECESIDAD":
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
        if pub_emisor.tipo == "TALENTO" and pub_receptor.tipo == "NECESIDAD":
            return (
                f"{nombre} te ofrece {pub_emisor.titulo} "
                f"para tu necesidad de {pub_receptor.titulo}."
            )
        if pub_emisor.tipo == "NECESIDAD" and pub_receptor.tipo == "TALENTO":
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
        _validar_usuario_no_comercio_trueques(emisor)

        if not receptor_id:
            raise BusinessError("Falta receptor_id.")

        try:
            receptor = Usuario.objects.obtener_por_id(receptor_id)
        except ObjectDoesNotExist:
            raise BusinessError("Receptor no encontrado.", status_code=404)

        _validar_usuario_no_comercio_trueques(receptor)

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

        trueque = AcuerdoTrueque.objects.obtener_o_crear_pendiente(
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
        _validar_usuario_no_comercio_trueques(receptor)

        try:
            trueque = AcuerdoTrueque.objects.obtener_por_receptor(trueque_id, receptor)
        except ObjectDoesNotExist:
            raise BusinessError("Propuesta no encontrada.", status_code=404)

        if accion == "ACEPTAR":
            trueque.estado = "ACEPTADO"
            AcuerdoTrueque.objects.guardar(trueque)
            self.notificacion_service.actualizar_estado_propuesta(trueque, "ACEPTADA")
            return "Propuesta aceptada. Confirma la finalización cuando el servicio esté completo."

        if accion == "RECHAZAR":
            trueque.estado = "RECHAZADO"
            AcuerdoTrueque.objects.guardar(trueque)
            self.notificacion_service.actualizar_estado_propuesta(trueque, "RECHAZADA")
            return "Propuesta rechazada."

        raise BusinessError("Accion invalida.")

    def finalizar_trueque(self, usuario, trueque_id):
        """Confirmación bilateral antes de transferir el saldo de horas."""
        _validar_usuario_no_comercio_trueques(usuario)

        with transaction.atomic():
            try:
                trueque = AcuerdoTrueque.objects.obtener_bloqueado(trueque_id)
            except ObjectDoesNotExist:
                raise BusinessError("Trueque no encontrado.", status_code=404)

            if usuario not in [trueque.emisor, trueque.receptor]:
                raise BusinessError("No eres parte de este trueque.", status_code=403)

            if trueque.estado != "ACEPTADO":
                raise BusinessError("El trueque debe estar aceptado para confirmar finalización.", status_code=400)

            if usuario == trueque.emisor:
                trueque.emisor_confirmado = True
            else:
                trueque.receptor_confirmado = True

            if not (trueque.emisor_confirmado and trueque.receptor_confirmado):
                AcuerdoTrueque.objects.guardar(trueque)
                return {
                    "saldo_transferido": False,
                    "impacto_horas": 0,
                    "habilitar_resena": False,
                    "mensaje": "Confirmación registrada. Esperando confirmación de la otra parte.",
                }

            if self._es_intercambio_mutuo(trueque):
                trueque.estado = "FINALIZADO"
                AcuerdoTrueque.objects.guardar(trueque)
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
            publicacion_necesidad = self._obtener_publicacion_necesidad_trueque(
                trueque,
                receptor_servicio,
            )

            prestador = Usuario.objects.obtener_por_id_bloqueado(prestador.id)
            receptor_servicio = Usuario.objects.obtener_por_id_bloqueado(receptor_servicio.id)

            tipo_pago = self._descontar_pago_trueque(receptor_servicio, publicacion_necesidad)

            prestador.horas_de_vida += 1.0
            Usuario.objects.guardar(prestador)
            if tipo_pago == "general":
                Usuario.objects.guardar(receptor_servicio)

            trueque.estado = "FINALIZADO"
            AcuerdoTrueque.objects.guardar(trueque)
            return {
                "saldo_transferido": True,
                "impacto_horas": 1,
                "habilitar_resena": True,
                "mensaje": "Trueque finalizado. Saldos actualizados. Sistema de reseñas habilitado.",
            }

    def listar_por_usuario(self, usuario):
        return AcuerdoTrueque.objects.listar_por_usuario(usuario)

    def obtener_por_participante(self, trueque_id, usuario):
        return AcuerdoTrueque.objects.obtener_por_participante(trueque_id, usuario)


class ResenaService(ResenaInterface):
    def registrar_resena(self, usuario, datos):
        trueque_id = datos.get("trueque_id")
        comentario = datos.get("comentario", "")

        try:
            estrellas = int(datos.get("estrellas"))
        except (TypeError, ValueError):
            raise BusinessError("Las estrellas deben ser un numero entero.")

        if estrellas < 1 or estrellas > 5:
            raise BusinessError("Las estrellas deben estar entre 1 y 5.")

        if len(comentario) > 500:
            raise BusinessError("El comentario no puede superar los 500 caracteres.")

        with transaction.atomic():
            try:
                trueque = AcuerdoTrueque.objects.obtener_bloqueado(trueque_id)
            except ObjectDoesNotExist:
                raise BusinessError("Trueque no encontrado.", status_code=404)

            if usuario not in [trueque.emisor, trueque.receptor]:
                raise BusinessError("No eres parte de este trueque.", status_code=403)

            if trueque.estado != "FINALIZADO":
                raise BusinessError("Solo se pueden dejar reseñas de trueques finalizados.", status_code=400)

            # Verificar si ya existe una reseña de este usuario para este trueque
            try:
                from .models import Resena
                Resena.objects.get(trueque=trueque, calificador=usuario)
                raise BusinessError("Ya has dejado una reseña para este trueque.", status_code=400)
            except Resena.DoesNotExist:
                pass  # No hay reseña previa, podemos continuar

            calificado = trueque.receptor if usuario == trueque.emisor else trueque.emisor
            Resena.objects.crear(trueque, usuario, calificado, estrellas, comentario)

        return "Resena registrada correctamente."


class ComercioService(ComercioInterface):
    def __init__(self):
        self.movimientos = []

    def emitir_vuelto(self, comercio, datos):
        if not comercio.es_comercio:
            raise BusinessError("Solo comercios pueden emitir saldos comerciales.", status_code=403)

        cliente_id = datos.get("cliente_id")
        if not cliente_id:
            raise BusinessError("Faltan datos.")

        monto, valor_producto, monto_recibido = self._resolver_excedente_emision(datos)

        if int(cliente_id) == comercio.id:
            raise BusinessError("Un comercio no puede emitir vuelto a si mismo.")

        with transaction.atomic():
            comercio_bloqueado = Usuario.objects.obtener_por_id_bloqueado(comercio.id)
            puede_emitir, mensaje = comercio_bloqueado.puede_emitir_vuelto_comercial(monto)
            if not puede_emitir:
                raise BusinessError(mensaje, status_code=403)

            try:
                cliente = Usuario.objects.obtener_por_id_bloqueado(cliente_id)
            except ObjectDoesNotExist:
                raise BusinessError("El cliente especificado no existe.", status_code=404)

            if cliente.es_comercio:
                raise BusinessError("No se puede emitir vuelto a otro comercio.")

            cliente.saldo_comercial += monto
            comercio_bloqueado.saldo_comercial -= monto
            Usuario.objects.guardar(cliente)
            Usuario.objects.guardar(comercio_bloqueado)

            movimiento = SaldoComercial.objects.crear_movimiento(
                comercio_bloqueado,
                cliente,
                monto,
                "EMISION",
                valor_producto=valor_producto,
                monto_recibido=monto_recibido,
            )
            self.movimientos.append(movimiento)

        return {
            "mensaje": "Saldo a favor comercial emitido correctamente (Inalterable en horas de vida).",
            "comprobante": movimiento,
            "saldo_cliente": cliente.saldo_comercial,
            "saldo_comercio": comercio_bloqueado.saldo_comercial,
        }

    def pagar_con_saldo(self, cliente, datos):
        comercio_id = datos.get("comercio_id")
        monto_valor = datos.get("monto")

        if not comercio_id or monto_valor in [None, ""]:
            raise BusinessError("Faltan datos.")

        monto = self._obtener_monto(monto_valor)

        if int(comercio_id) == cliente.id:
            raise BusinessError("No puede pagar en su propio comercio.")

        with transaction.atomic():
            cliente_bloqueado = Usuario.objects.obtener_por_id_bloqueado(cliente.id)

            puede_pagar, mensaje = cliente_bloqueado.puede_pagar_con_saldo(monto)
            if not puede_pagar:
                raise BusinessError(mensaje)

            try:
                comercio = Usuario.objects.obtener_por_id_bloqueado(comercio_id)
            except ObjectDoesNotExist:
                raise BusinessError("Comercio no encontrado.", status_code=404)

            if not comercio.es_comercio_activo():
                raise BusinessError("El usuario de destino no es un comercio activo.")

            cliente_bloqueado.saldo_comercial -= monto
            comercio.saldo_comercial += monto
            Usuario.objects.guardar(cliente_bloqueado)
            Usuario.objects.guardar(comercio)

            movimiento = SaldoComercial.objects.crear_movimiento(
                comercio, cliente_bloqueado, monto, "PAGO"
            )
            self.movimientos.append(movimiento)

        return {
            "mensaje": "Pago procesado con exito utilizando saldo comercial.",
            "comprobante": movimiento,
            "saldo_restante": cliente_bloqueado.saldo_comercial,
            "saldo_comercio": comercio.saldo_comercial,
        }

    def listar_comercios(self):
        comercios = Usuario.objects.listar_comercios_activos()
        return [comercio for comercio in comercios if comercio.es_comercio_activo()]

    def listar_clientes(self, termino_busqueda=None):
        clientes = Usuario.objects.filter(
            es_comercio=False,
            is_active=True,
            is_staff=False,
            is_superuser=False,
        ).order_by('nombre_real', 'username')

        if termino_busqueda:
            termino = str(termino_busqueda).strip()
            if termino:
                clientes = clientes.filter(
                    Q(nombre_real__icontains=termino) | Q(username__icontains=termino)
                )

        return list(clientes)

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


class NotificacionService:
    def crear_notificacion_propuesta(
        self,
        destinatario,
        remitente,
        trueque,
        publicacion_original,
        mensaje,
        tipo="PROPUESTA",
    ):
        return NotificacionPropuesta.objects.crear_notificacion(
            destinatario,
            remitente,
            trueque,
            publicacion_original,
            mensaje,
            tipo=tipo,
        )

    def actualizar_estado_propuesta(self, trueque, estado):
        return NotificacionPropuesta.objects.actualizar_estado_por_trueque(trueque, estado)
    
    def obtener_notificaciones_usuario(self, usuario, incluir_leidas=False):
        return NotificacionPropuesta.objects.obtener_notificaciones_usuario(
            usuario,
            incluir_leidas=incluir_leidas,
        )
    
    def marcar_notificacion_leida(self, notificacion_id, usuario):
        try:
            return NotificacionPropuesta.objects.marcar_como_leida(
                notificacion_id,
                destinatario=usuario,
            )
        except ObjectDoesNotExist:
            raise BusinessError("Notificación no encontrada.", status_code=404)

    def marcar_notificaciones_trueque_leidas(self, usuario, trueque_id):
        actualizadas = NotificacionPropuesta.objects.marcar_leidas_por_trueque(
            usuario,
            trueque_id,
        )
        return actualizadas


class MatchmakingService(MatchmakingInterface):
    def __init__(self):
        self.matches = []

    @staticmethod
    def _construir_match_enriquecido(usuario, candidato, titulos_necesidades, titulos_talentos):
        mis_talentos = list(
            Publicacion.objects.filter(
                usuario=usuario,
                tipo="TALENTO",
                esta_activa=True,
                titulo__in=titulos_talentos,
            ),
        )
        mis_necesidades = list(
            Publicacion.objects.filter(
                usuario=usuario,
                tipo="NECESIDAD",
                esta_activa=True,
                titulo__in=titulos_necesidades,
            ),
        )
        talentos_coincidentes = list(
            Publicacion.objects.filter(
                usuario=candidato,
                tipo="TALENTO",
                esta_activa=True,
                titulo__in=titulos_necesidades,
            ),
        )
        necesidades_coincidentes = list(
            Publicacion.objects.filter(
                usuario=candidato,
                tipo="NECESIDAD",
                esta_activa=True,
                titulo__in=titulos_talentos,
            ),
        )

        publicaciones_sugeridas = []
        for mi_nec in mis_necesidades:
            for su_tal in talentos_coincidentes:
                if mi_nec.titulo == su_tal.titulo:
                    publicaciones_sugeridas.append(
                        {"mi_pub_id": mi_nec.id, "su_pub_id": su_tal.id},
                    )
        for mi_tal in mis_talentos:
            for su_nec in necesidades_coincidentes:
                if mi_tal.titulo == su_nec.titulo:
                    publicaciones_sugeridas.append(
                        {"mi_pub_id": mi_tal.id, "su_pub_id": su_nec.id},
                    )

        return {
            "usuario": candidato,
            "talentos_coincidentes": talentos_coincidentes,
            "necesidades_coincidentes": necesidades_coincidentes,
            "publicaciones_sugeridas": publicaciones_sugeridas,
        }

    def buscar_matches(self, usuario, titulos_necesidades, titulos_talentos):
        candidatos = Usuario.objects.buscar_candidatos_match(
            usuario,
            titulos_necesidades,
            titulos_talentos,
        )
        return [
            self._construir_match_enriquecido(
                usuario,
                candidato,
                titulos_necesidades,
                titulos_talentos,
            )
            for candidato in candidatos
        ]

    def buscar_matches_por_publicacion(self, usuario, publicacion):
        if not publicacion or not publicacion.titulo:
            return []

        tipo_buscado = "NECESIDAD" if publicacion.tipo == "TALENTO" else "TALENTO"
        tipo_propio = "TALENTO" if publicacion.tipo == "NECESIDAD" else "NECESIDAD"
        candidatos = Usuario.objects.buscar_candidatos_por_publicacion(usuario, publicacion)
        resultados = []

        for candidato in candidatos:
            pubs_complementarias = list(
                Publicacion.objects.filter(
                    usuario=candidato,
                    tipo=tipo_buscado,
                    titulo=publicacion.titulo,
                    esta_activa=True,
                ),
            )
            mis_complementarias = list(
                Publicacion.objects.filter(
                    usuario=usuario,
                    tipo=tipo_propio,
                    esta_activa=True,
                ),
            )
            titulos_mis_complementarias = {pub.titulo for pub in mis_complementarias}
            talentos_coincidentes = []
            necesidades_coincidentes = []

            if tipo_buscado == "TALENTO":
                talentos_coincidentes = pubs_complementarias
                necesidades_coincidentes = list(
                    Publicacion.objects.filter(
                        usuario=candidato,
                        tipo="NECESIDAD",
                        titulo__in=titulos_mis_complementarias,
                        esta_activa=True,
                    ),
                )
            else:
                necesidades_coincidentes = pubs_complementarias
                talentos_coincidentes = list(
                    Publicacion.objects.filter(
                        usuario=candidato,
                        tipo="TALENTO",
                        titulo__in=titulos_mis_complementarias,
                        esta_activa=True,
                    ),
                )

            if not talentos_coincidentes or not necesidades_coincidentes:
                continue

            titulos_necesidades = (
                [publicacion.titulo]
                if publicacion.tipo == "NECESIDAD"
                else [pub.titulo for pub in necesidades_coincidentes]
            )
            titulos_talentos = (
                [publicacion.titulo]
                if publicacion.tipo == "TALENTO"
                else [pub.titulo for pub in talentos_coincidentes]
            )
            resultados.append(
                self._construir_match_enriquecido(
                    usuario,
                    candidato,
                    titulos_necesidades,
                    titulos_talentos,
                ),
            )

        return resultados

    def obtener_matches(self, usuario):
        titulos_necesidades = Publicacion.objects.titulos_activos_por_usuario_y_tipo(
            usuario,
            "NECESIDAD",
        )
        titulos_talentos = Publicacion.objects.titulos_activos_por_usuario_y_tipo(
            usuario,
            "TALENTO",
        )
        self.matches = self.buscar_matches(usuario, titulos_necesidades, titulos_talentos)
        return self.matches

    def verificar_coincidencia_por_titulo(self, usuario, publicacion_id):
        try:
            publicacion = Publicacion.objects.get(id=publicacion_id, esta_activa=True)
            return Publicacion.objects.verificar_coincidencia_por_titulo(usuario, publicacion)
        except Publicacion.DoesNotExist:
            return {
                "tiene_coincidencia": False,
                "publicaciones_coincidentes": [],
                "tipo_buscado": None,
                "titulo": None,
                "error": "Publicación no encontrada",
            }

    def obtener_matches_por_publicacion(self, usuario, publicacion_id):
        try:
            publicacion = Publicacion.objects.get(id=publicacion_id, esta_activa=True)
            self.matches = self.buscar_matches_por_publicacion(usuario, publicacion)
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
        if usuario.es_comercio:
            return []

        matches = self.obtener_matches(usuario)
        notificaciones_creadas = []

        for match in matches:
            otro_usuario = match["usuario"]
            if NotificacionPropuesta.objects.existe_match_entre(usuario, otro_usuario):
                continue

            pub_emisor, pub_receptor = self._resolver_publicaciones_match_completo(match, usuario)

            if not pub_emisor:
                sugerencia = match["publicaciones_sugeridas"][0] if match["publicaciones_sugeridas"] else {}
                if sugerencia:
                    from .models import Publicacion

                    pub_emisor = Publicacion.objects.filter(id=sugerencia.get("mi_pub_id")).first()
                    pub_receptor = Publicacion.objects.filter(id=sugerencia.get("su_pub_id")).first()

            trueque = AcuerdoTrueque.objects.obtener_o_crear_pendiente(
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
                NotificacionPropuesta.objects.crear_notificacion(
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
                NotificacionPropuesta.objects.crear_notificacion(
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


class PerfilService:
    def obtener_perfil_publico(self, usuario_id):
        usuario = Usuario.objects.obtener_por_id(usuario_id)
        publicaciones_activas = Publicacion.objects.listar_por_usuario(usuario, solo_activas=True)
        resenas_recibidas = Resena.objects.listar_por_calificado(usuario)
        return usuario, publicaciones_activas, resenas_recibidas

    def obtener_mi_perfil(self, usuario):
        publicaciones = Publicacion.objects.listar_por_usuario(usuario)
        publicaciones_activas = [publicacion for publicacion in publicaciones if publicacion.esta_activa]
        publicaciones_pausadas = [publicacion for publicacion in publicaciones if not publicacion.esta_activa]
        resenas_recibidas = Resena.objects.listar_por_calificado(usuario)
        trueques_enviados = AcuerdoTrueque.objects.filter(emisor=usuario)
        trueques_recibidos = AcuerdoTrueque.objects.filter(receptor=usuario)
        return {
            "publicaciones": publicaciones,
            "publicaciones_activas": publicaciones_activas,
            "publicaciones_pausadas": publicaciones_pausadas,
            "resenas_recibidas": resenas_recibidas,
            "trueques_enviados_count": trueques_enviados.count(),
            "trueques_recibidos_count": trueques_recibidos.count(),
        }

    def listar_mis_publicaciones(self, usuario):
        return Publicacion.objects.listar_por_usuario(usuario)


class ComunidadService:
    @staticmethod
    def es_miembro_activo(usuario):
        nombre = (usuario.nombre_real or "").strip()
        return bool(nombre and Publicacion.objects.filter(usuario=usuario).exists())

    def obtener_directorio(self):
        miembros = Usuario.objects.filter(
            is_active=True,
            is_staff=False,
            is_superuser=False,
        ).order_by("nombre_real", "username")

        directorio = []
        for miembro in miembros:
            publicaciones = Publicacion.objects.listar_por_usuario(miembro)
            talentos_activos = [
                publicacion for publicacion in publicaciones
                if publicacion.tipo == "TALENTO" and publicacion.esta_activa
            ]
            directorio.append({
                "id": miembro.id,
                "nombre_real": miembro.nombre_real,
                "username": miembro.username,
                "promedio_estrellas": miembro.promedio_estrellas,
                "talentos_principales": [publicacion.titulo for publicacion in talentos_activos[:3]],
                "cantidad_talentos": len(talentos_activos),
                "es_miembro_activo": self.es_miembro_activo(miembro),
            })

        return directorio


MENSAJE_SALDO_POSITIVO_DONACION = "Necesitas saldo positivo para realizar donaciones solidarias"
MENSAJE_TIEMPO_PRESTADO = "No puedes donar tiempo prestado"
MENSAJE_MONTO_MINIMO_DONACION = "El monto mínimo de donación es 0.5 horas"
MENSAJE_COMERCIO_NO_IMPACTO_SOCIAL = "Los comercios no pueden realizar donaciones solidarias"
MENSAJE_RECEPTOR_MAS_10_HORAS = "Usuarios con más de 10 horas no pueden recibir donaciones"
MENSAJE_TOPE_HORAS_RECIBIDAS = "No se puede donar más de 10 horas a este usuario"
MENSAJE_SOLO_VULNERABLE_CRITICO = "Solo se puede asignar a usuarios vulnerables o críticos"
MENSAJE_DONACION_EXITOSA = "Donación Exitosa"
MENSAJE_NO_DONAR_PROPIA_CAUSA = "No puedes donar horas a tu propia causa."
MENSAJE_SOLICITUD_ASIGNACION_REQUERIDA = "Debes indicar la solicitud a la que asignar las horas."
MENSAJE_SIN_SOLICITUD_APROBADA = "El usuario no tiene solicitudes aprobadas."
MENSAJE_SOLICITUD_NO_PERTENECE_RECEPTOR = "La solicitud no pertenece al usuario receptor."
MENSAJE_SOLICITUD_NO_APROBADA_ACTIVAR = "Solo puedes activar necesidades de solicitudes aprobadas."
MENSAJE_NECESIDAD_YA_VINCULADA = "Esta solicitud ya tiene una necesidad vinculada."
MENSAJE_NO_ACTIVAR_SOLICITUD_AJENA = "No puedes activar la necesidad de una solicitud ajena."
MENSAJE_SIN_PERMISOS_ADMIN = "No tienes permisos de administrador."
MENSAJE_TITULO_CAUSA_INVALIDO = "El título seleccionado no corresponde a una causa social permitida."
MENSAJE_CATEGORIA_CAUSA_INVALIDA = "La categoría seleccionada no es válida para causas sociales."
MENSAJE_CATEGORIA_TITULO_INCONSISTENTES = "El título no pertenece a la categoría seleccionada."
MENSAJE_SOLICITANTE_MARCADO_VULNERABLE = (
    "Solicitud aprobada. El solicitante fue catalogado como Usuario Vulnerable."
)


def _validar_usuario_no_comercio_impacto_social(usuario):
    if usuario.es_comercio:
        raise BusinessError(MENSAJE_COMERCIO_NO_IMPACTO_SOCIAL, status_code=403)


def _validar_admin_impacto_social(admin):
    if not (admin.is_staff or admin.is_superuser):
        raise BusinessError(MENSAJE_SIN_PERMISOS_ADMIN, status_code=403)


def _validar_monto_donacion(monto):
    try:
        monto = float(monto)
    except (TypeError, ValueError):
        raise BusinessError(MENSAJE_MONTO_MINIMO_DONACION)

    if monto < 0.5:
        raise BusinessError(MENSAJE_MONTO_MINIMO_DONACION)
    return monto


def _validar_donante_puede_donar(donante, monto):
    _validar_usuario_no_comercio_impacto_social(donante)

    if donante.horas_de_vida <= 0:
        raise BusinessError(MENSAJE_SALDO_POSITIVO_DONACION)

    if donante.horas_de_vida - monto < 0:
        raise BusinessError(MENSAJE_TIEMPO_PRESTADO)


def _validar_receptor_puede_recibir_donacion(receptor, monto):
    if receptor.es_fondo_comunitario:
        return

    if receptor.horas_de_vida > 10:
        raise BusinessError(MENSAJE_RECEPTOR_MAS_10_HORAS)

    if receptor.horas_recibidas_donacion + monto > 10:
        raise BusinessError(MENSAJE_TOPE_HORAS_RECIBIDAS)


def _resolver_solicitud_asignacion_fondo(receptor, solicitud_id):
    if solicitud_id is not None:
        try:
            solicitud = SolicitudApoyoSocial.objects.get(id=solicitud_id)
        except ObjectDoesNotExist:
            raise BusinessError("Solicitud no encontrada.", status_code=404)
    else:
        solicitudes_aprobadas = SolicitudApoyoSocial.objects.filter(
            solicitante_id=receptor.id,
            estado="APROBADA",
        )
        cantidad = solicitudes_aprobadas.count()
        if cantidad == 0:
            raise BusinessError(MENSAJE_SIN_SOLICITUD_APROBADA)
        if cantidad > 1:
            raise BusinessError(MENSAJE_SOLICITUD_ASIGNACION_REQUERIDA)
        solicitud = solicitudes_aprobadas.first()

    if solicitud.estado != "APROBADA":
        raise BusinessError("Solo se puede asignar a solicitudes aprobadas.")
    if solicitud.solicitante_id != receptor.id:
        raise BusinessError(MENSAJE_SOLICITUD_NO_PERTENECE_RECEPTOR)
    return solicitud


def _obtener_fondo_comunitario():
    try:
        return Usuario.objects.get(username="fondo_comunitario", es_fondo_comunitario=True)
    except ObjectDoesNotExist:
        raise BusinessError("Fondo comunitario no configurado.", status_code=500)


class ImpactoSocialService:
    """Sprint 2 HU1: Donaciones solidarias y gestión de apoyo social."""

    def crear_solicitud(self, usuario, datos):
        _validar_usuario_no_comercio_impacto_social(usuario)

        categoria = (datos.get("categoria") or "").strip()
        if not categoria or not es_categoria_causa_social_permitida(categoria):
            raise BusinessError(MENSAJE_CATEGORIA_CAUSA_INVALIDA)

        titulo = (datos.get("titulo") or "").strip()
        if not titulo or not es_titulo_causa_social_permitido(titulo):
            raise BusinessError(MENSAJE_TITULO_CAUSA_INVALIDO)

        if categoria_para_titulo(titulo) != categoria:
            raise BusinessError(MENSAJE_CATEGORIA_TITULO_INCONSISTENTES)

        descripcion = (datos.get("descripcion") or "").strip()
        if not descripcion:
            raise BusinessError("Título y descripción son obligatorios.")

        return SolicitudApoyoSocial.objects.create(
            solicitante=usuario,
            categoria=categoria,
            titulo=titulo,
            descripcion=descripcion,
            estado="PENDIENTE",
        )

    def listar_solicitudes_aprobadas(self):
        solicitudes = SolicitudApoyoSocial.objects.filter(
            estado="APROBADA",
        ).select_related("solicitante").order_by("-id")

        return [
            {
                "id": solicitud.id,
                "categoria": solicitud.categoria,
                "titulo": solicitud.titulo,
                "descripcion": solicitud.descripcion,
                "horas_recibidas": solicitud.horas_recibidas,
                "estado_social_solicitante": solicitud.solicitante.estado_social,
                "solicitante_id": solicitud.solicitante_id,
                "solicitante_nombre": solicitud.solicitante.nombre_real,
                "horas_recibidas_donacion_solicitante": solicitud.solicitante.horas_recibidas_donacion,
                "horas_de_vida_solicitante": solicitud.solicitante.horas_de_vida,
            }
            for solicitud in solicitudes
        ]

    def listar_mis_solicitudes(self, usuario):
        return list(
            SolicitudApoyoSocial.objects.filter(solicitante=usuario)
            .select_related("publicacion")
            .order_by("-id"),
        )

    def activar_necesidad_vinculada(self, usuario, solicitud_id):
        """Publica una NECESIDAD en cartelera vinculada a una solicitud aprobada.

        Las publicaciones es_causa_social=True no cuentan contra el límite de 3
        necesidades activas de la cartelera. Urgencia ALTA por defecto (causa validada).
        """
        _validar_usuario_no_comercio_impacto_social(usuario)

        try:
            solicitud = SolicitudApoyoSocial.objects.select_related("publicacion").get(id=solicitud_id)
        except ObjectDoesNotExist:
            raise BusinessError("Solicitud no encontrada.", status_code=404)

        if solicitud.solicitante_id != usuario.id:
            raise BusinessError(MENSAJE_NO_ACTIVAR_SOLICITUD_AJENA)

        if solicitud.estado != "APROBADA":
            raise BusinessError(MENSAJE_SOLICITUD_NO_APROBADA_ACTIVAR)

        if solicitud.publicacion_id is not None:
            raise BusinessError(MENSAJE_NECESIDAD_YA_VINCULADA)

        with transaction.atomic():
            publicacion = Publicacion.objects.create(
                usuario=usuario,
                tipo="NECESIDAD",
                titulo=solicitud.titulo,
                descripcion=solicitud.descripcion,
                categoria=solicitud.categoria,
                urgencia="ALTA",
                es_causa_social=True,
                esta_activa=True,
            )
            solicitud.publicacion = publicacion
            solicitud.save(update_fields=["publicacion"])

        MatchmakingService().detectar_y_notificar_matches(usuario)
        solicitud.refresh_from_db()
        return solicitud

    def listar_solicitudes_pendientes(self, admin):
        _validar_admin_impacto_social(admin)
        return list(
            SolicitudApoyoSocial.objects.filter(estado="PENDIENTE")
            .select_related("solicitante")
            .order_by("creado_el"),
        )

    def aprobar_solicitud(self, admin, solicitud_id):
        _validar_admin_impacto_social(admin)

        try:
            solicitud = SolicitudApoyoSocial.objects.get(id=solicitud_id)
        except ObjectDoesNotExist:
            raise BusinessError("Solicitud no encontrada.", status_code=404)

        if solicitud.estado != "PENDIENTE":
            raise BusinessError("Solo se pueden aprobar solicitudes pendientes.")

        marcado_vulnerable = False
        with transaction.atomic():
            solicitud.estado = "APROBADA"
            solicitud.aprobada_por = admin
            solicitud.save(update_fields=["estado", "aprobada_por"])

            solicitante = Usuario.objects.select_for_update().get(id=solicitud.solicitante_id)
            if solicitante.estado_social == "NINGUNO":
                solicitante.estado_social = "VULNERABLE"
                solicitante.save(update_fields=["estado_social"])
                marcado_vulnerable = True

        solicitud.refresh_from_db()
        solicitud.solicitante.refresh_from_db()
        solicitud.solicitante_marcado_vulnerable = marcado_vulnerable
        return solicitud

    def rechazar_solicitud(self, admin, solicitud_id):
        _validar_admin_impacto_social(admin)

        try:
            solicitud = SolicitudApoyoSocial.objects.get(id=solicitud_id)
        except ObjectDoesNotExist:
            raise BusinessError("Solicitud no encontrada.", status_code=404)

        if solicitud.estado != "PENDIENTE":
            raise BusinessError("Solo se pueden rechazar solicitudes pendientes.")

        solicitud.estado = "RECHAZADA"
        solicitud.aprobada_por = admin
        solicitud.save()
        return solicitud

    def actualizar_estado_social(self, admin, usuario_id, estado_social):
        _validar_admin_impacto_social(admin)

        estados_validos = {choice[0] for choice in Usuario.ESTADO_SOCIAL_CHOICES}
        if estado_social not in estados_validos:
            raise BusinessError("Estado social inválido.")

        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except ObjectDoesNotExist:
            raise BusinessError("Usuario no encontrado.", status_code=404)

        if usuario.es_fondo_comunitario or usuario.es_comercio:
            raise BusinessError("No se puede modificar el estado social de este usuario.")

        usuario.estado_social = estado_social
        usuario.save(update_fields=["estado_social"])
        return usuario

    def listar_usuarios_para_admin(self, admin):
        _validar_admin_impacto_social(admin)
        return list(
            Usuario.objects.filter(
                is_active=True,
                es_comercio=False,
                is_staff=False,
                is_superuser=False,
                es_fondo_comunitario=False,
            ).order_by("nombre_real", "username"),
        )

    def obtener_saldo_fondo(self, admin=None):
        if admin is not None:
            _validar_admin_impacto_social(admin)

        fondo = _obtener_fondo_comunitario()
        return {
            "saldo": fondo.horas_de_vida,
            "username": fondo.username,
        }

    def donar_a_causa(self, donante, solicitud_id, monto):
        monto = _validar_monto_donacion(monto)

        try:
            solicitud = SolicitudApoyoSocial.objects.select_related("solicitante").get(id=solicitud_id)
        except ObjectDoesNotExist:
            raise BusinessError("Solicitud no encontrada.", status_code=404)

        if solicitud.estado != "APROBADA":
            raise BusinessError("Solo se puede donar a solicitudes aprobadas.")

        if donante.id == solicitud.solicitante_id:
            raise BusinessError(MENSAJE_NO_DONAR_PROPIA_CAUSA)

        return self._ejecutar_donacion(
            donante=donante,
            receptor=solicitud.solicitante,
            monto=monto,
            tipo_destino="CAUSA",
            solicitud=solicitud,
        )

    def donar_a_fondo(self, donante, monto):
        monto = _validar_monto_donacion(monto)
        fondo = _obtener_fondo_comunitario()
        return self._ejecutar_donacion(
            donante=donante,
            receptor=fondo,
            monto=monto,
            tipo_destino="FONDO",
            solicitud=None,
        )

    def asignar_desde_fondo(self, admin, usuario_id, monto, solicitud_id=None):
        _validar_admin_impacto_social(admin)
        monto = _validar_monto_donacion(monto)

        try:
            receptor = Usuario.objects.get(id=usuario_id)
        except ObjectDoesNotExist:
            raise BusinessError("Usuario no encontrado.", status_code=404)

        if receptor.estado_social not in ("VULNERABLE", "CRITICO"):
            raise BusinessError(MENSAJE_SOLO_VULNERABLE_CRITICO)

        solicitud = _resolver_solicitud_asignacion_fondo(receptor, solicitud_id)
        _validar_receptor_puede_recibir_donacion(receptor, monto)

        with transaction.atomic():
            fondo = Usuario.objects.obtener_por_id_bloqueado(
                _obtener_fondo_comunitario().id,
            )
            receptor = Usuario.objects.obtener_por_id_bloqueado(receptor.id)
            solicitud = SolicitudApoyoSocial.objects.select_for_update().get(id=solicitud.id)

            if fondo.horas_de_vida < monto:
                raise BusinessError("El fondo comunitario no tiene saldo suficiente.")

            fondo.horas_de_vida -= monto
            receptor.horas_recibidas_donacion += monto
            solicitud.horas_solidarias_disponibles += monto
            solicitud.horas_recibidas += monto
            solicitud.save(update_fields=["horas_solidarias_disponibles", "horas_recibidas"])
            Usuario.objects.guardar(fondo)
            Usuario.objects.guardar(receptor)

            donacion = DonacionHoras.objects.create(
                donante=fondo,
                receptor=receptor,
                solicitud=solicitud,
                monto=monto,
                tipo_destino="ASIGNACION",
            )

        return {
            "mensaje": "Asignación desde fondo realizada.",
            "monto": monto,
            "receptor_id": receptor.id,
            "solicitud_id": solicitud.id,
            "horas_solidarias_disponibles": solicitud.horas_solidarias_disponibles,
            "saldo_fondo": fondo.horas_de_vida,
            "saldo_receptor": receptor.horas_de_vida,
            "donacion_id": donacion.id,
            "comprobante_id": str(donacion.comprobante_id),
        }

    def listar_mis_donaciones_realizadas(self, usuario):
        return DonacionHoras.objects.filter(
            donante=usuario,
        ).select_related("donante", "receptor", "solicitud").order_by("-fecha")

    def listar_mis_donaciones_recibidas(self, usuario):
        return DonacionHoras.objects.filter(
            receptor=usuario,
        ).select_related("donante", "receptor", "solicitud").order_by("-fecha")

    def _ejecutar_donacion(self, donante, receptor, monto, tipo_destino, solicitud):
        with transaction.atomic():
            donante = Usuario.objects.obtener_por_id_bloqueado(donante.id)
            receptor = Usuario.objects.obtener_por_id_bloqueado(receptor.id)

            _validar_donante_puede_donar(donante, monto)
            _validar_receptor_puede_recibir_donacion(receptor, monto)

            if solicitud is not None:
                solicitud = SolicitudApoyoSocial.objects.select_for_update().get(id=solicitud.id)

            donante.horas_de_vida -= monto

            if tipo_destino == "CAUSA":
                receptor.horas_recibidas_donacion += monto
                solicitud.horas_solidarias_disponibles += monto
                solicitud.horas_recibidas += monto
                solicitud.save(update_fields=["horas_solidarias_disponibles", "horas_recibidas"])
            else:
                receptor.horas_de_vida += monto

            donacion = DonacionHoras.objects.create(
                donante=donante,
                receptor=receptor,
                solicitud=solicitud,
                monto=monto,
                tipo_destino=tipo_destino,
            )
            Usuario.objects.guardar(donante)
            Usuario.objects.guardar(receptor)

        return {
            "mensaje": MENSAJE_DONACION_EXITOSA,
            "monto": monto,
            "tipo_destino": tipo_destino,
            "receptor_id": receptor.id,
            "receptor_nombre": receptor.nombre_real,
            "saldo_restante": donante.horas_de_vida,
            "comprobante_id": str(donacion.comprobante_id),
            "donacion_id": donacion.id,
        }

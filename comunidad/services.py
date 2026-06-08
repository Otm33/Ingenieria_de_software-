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
    def __init__(self, publicacion_repository=None):
        self.publicacion_repository = publicacion_repository or PublicacionRepository()

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

        if contiene_palabra_prohibida(titulo) or contiene_palabra_prohibida(descripcion):
            raise BusinessError("La publicación contiene palabras no permitidas.")

        return self.publicacion_repository.crear(usuario, {
            "tipo": tipo,
            "titulo": titulo,
            "descripcion": descripcion,
            "categoria": categoria,
            "urgencia": urgencia,
        })

    def pausar_publicacion(self, usuario, publicacion_id):
        return self.actualizar_estado_publicacion(usuario, publicacion_id, esta_activa=False)

    def reactivar_publicacion(self, usuario, publicacion_id):
        return self.actualizar_estado_publicacion(usuario, publicacion_id, esta_activa=True)

    def actualizar_estado_publicacion(self, usuario, publicacion_id, esta_activa):
        from .models import Publicacion

        if usuario.horas_de_vida < -10:
            raise BusinessError("Saldo crítico inferior a -10 horas. No puedes modificar ofertas.")

        try:
            publicacion = self.publicacion_repository.obtener_por_id_y_usuario(publicacion_id, usuario)
        except Publicacion.DoesNotExist:
            raise BusinessError("Publicación no encontrada.", status_code=404)

        # Solo validar limites cuando se re-activan publicaciones
        if esta_activa and not publicacion.esta_activa:
            conteo_activas = self.publicacion_repository.contar_activas_por_tipo(usuario, publicacion.tipo)
            if publicacion.tipo == "TALENTO" and conteo_activas >= 5:
                raise BusinessError("No puedes tener más de 5 talentos activos publicados simultáneamente.")
            if publicacion.tipo == "NECESIDAD" and conteo_activas >= 3:
                raise BusinessError("No puedes tener más de 3 necesidades activas simultáneamente.")

        publicacion.esta_activa = esta_activa
        publicacion.save(update_fields=["esta_activa"])
        return publicacion


class CarteleraService(CarteleraInterface):
    def __init__(self, publicacion_repository=None):
        self.publicacion_repository = publicacion_repository or PublicacionRepository()

    def obtener_publicaciones(self, categoria=None, urgencia=None):
        return self.publicacion_repository.obtener_cartelera(categoria=categoria, urgencia=urgencia)


class TruequeService(TruequeInterface):
    def __init__(self, trueque_repository=None, usuario_repository=None, publicacion_repository=None, notificacion_service=None):
        self.trueque_repository = trueque_repository or AcuerdoTruequeRepository()
        self.usuario_repository = usuario_repository or UsuarioRepository()
        self.publicacion_repository = publicacion_repository or PublicacionRepository()
        self.notificacion_service = notificacion_service or NotificacionService()

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

        trueque = self.trueque_repository.crear(
            emisor=emisor, 
            receptor=receptor,
            publicacion_emisor=pub_emisor,
            publicacion_receptor=pub_receptor
        )
        
        # Crear notificación para el receptor
        if pub_emisor:
            mensaje = f"{emisor.nombre_real} está interesado en tu {pub_emisor.tipo.lower()}: {pub_emisor.titulo}"
            self.notificacion_service.crear_notificacion_propuesta(
                destinatario=receptor,
                remitente=emisor,
                trueque=trueque,
                publicacion_original=pub_emisor,
                mensaje=mensaje
            )
        
        return trueque

    def responder_propuesta(self, receptor, trueque_id, accion):
        try:
            trueque = self.trueque_repository.obtener_por_receptor(trueque_id, receptor)
        except ObjectDoesNotExist:
            raise BusinessError("Propuesta no encontrada.", status_code=404)

        if accion == "ACEPTAR":
            trueque.estado = "EN_CURSO"
            self.trueque_repository.guardar(trueque)
            return "Propuesta aceptada. Intercambio en curso."

        if accion == "RECHAZAR":
            trueque.estado = "RECHAZADO"
            self.trueque_repository.guardar(trueque)
            return "Propuesta rechazada."

        raise BusinessError("Accion invalida.")

    def finalizar_trueque(self, usuario, trueque_id):
        """Finaliza el trueque cuando el usuario con necesidad confirma que el servicio fue completado."""
        with transaction.atomic():
            try:
                trueque = self.trueque_repository.obtener_bloqueado(trueque_id)
            except ObjectDoesNotExist:
                raise BusinessError("Trueque no encontrado.", status_code=404)

            # Verificar que el usuario sea parte del trueque
            if usuario != trueque.emisor and usuario != trueque.receptor:
                raise BusinessError("No eres parte de este trueque.", status_code=403)

            # Verificar que el trueque esté en curso
            if trueque.estado != "EN_CURSO":
                raise BusinessError("El trueque no está en curso.", status_code=400)

            # Verificar que el usuario con necesidad sea quien finaliza
            if trueque.publicacion_emisor and trueque.publicacion_emisor.tipo == "TALENTO":
                # El emisor tiene el talento, el receptor tiene la necesidad
                if usuario != trueque.receptor:
                    raise BusinessError("Solo el usuario con necesidad puede finalizar el trueque.", status_code=403)
            elif trueque.publicacion_receptor and trueque.publicacion_receptor.tipo == "NECESIDAD":
                # El receptor tiene la necesidad
                if usuario != trueque.receptor:
                    raise BusinessError("Solo el usuario con necesidad puede finalizar el trueque.", status_code=403)

            # Verificar límite de balance negativo
            emisor = trueque.emisor
            receptor = trueque.receptor

            if emisor.horas_de_vida - 1.0 < -10.0:
                raise BusinessError("El emisor tiene un límite de balance negativo excedido (-10).")

            # Transferir las horas (el que dio el servicio pierde una hora, el que recibió gana una hora)
            emisor.horas_de_vida -= 1.0
            receptor.horas_de_vida += 1.0
            self.usuario_repository.guardar(emisor)
            self.usuario_repository.guardar(receptor)

            trueque.estado = "FINALIZADO"
            self.trueque_repository.guardar(trueque)
            return "Trueque finalizado. Saldos actualizados. Sistema de reseñas habilitado."


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


class NotificacionService:
    def __init__(self, notificacion_repository=None):
        self.notificacion_repository = notificacion_repository or NotificacionPropuestaRepository()
    
    def crear_notificacion_propuesta(self, destinatario, remitente, trueque, publicacion_original, mensaje):
        return self.notificacion_repository.crear_notificacion(
            destinatario, remitente, trueque, publicacion_original, mensaje
        )
    
    def obtener_notificaciones_usuario(self, usuario):
        return self.notificacion_repository.obtener_notificaciones_usuario(usuario)
    
    def marcar_notificacion_leida(self, notificacion_id):
        return self.notificacion_repository.marcar_como_leida(notificacion_id)


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

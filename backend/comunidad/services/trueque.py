import time

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from .base import BusinessError, generar_codigo_confirmacion
from ..interfaces.service_interfaces import TruequeInterface
from ..repositorios_implementacion import TruequeRepository, UsuarioRepository, PublicacionRepository
from .notificacion import NotificacionService
from ..negocio.trueque import (
    es_intercambio_mutuo, esta_en_curso, puede_confirmar,
    ambas_partes_confirmaron, es_participante, contraparte,
    autorizar_actor_finalizacion, autorizar_actor_codigo,
)
from ..negocio.publicacion import es_talento, es_necesidad
# Audit log para medir la metrica de autorizacion
from ..negocio.audit_log import registrar_intento_autorizacion, AUTORIZADO, BLOQUEADO


class TruequeService(TruequeInterface):
    def __init__(self, trueque_repository=None, usuario_repository=None, publicacion_repository=None, notificacion_service=None):
        self.trueque_repository = trueque_repository or TruequeRepository()
        self.usuario_repository = usuario_repository or UsuarioRepository()
        self.publicacion_repository = publicacion_repository or PublicacionRepository()
        self.notificacion_service = notificacion_service or NotificacionService()

    @staticmethod
    def _es_intercambio_mutuo(trueque):
        """Trueque complementario: ambas partes ofrecen un TALENTO (impacto 0 horas).

        Resuelve los tipos de publicación desde relaciones ORM disponibles
        y delega a la función pura de negocio.
        """
        pub_emisor = getattr(trueque, 'publicacion_emisor', None)
        pub_receptor = getattr(trueque, 'publicacion_receptor', None)
        tipo_emisor = getattr(pub_emisor, 'tipo', None) if pub_emisor else None
        tipo_receptor = getattr(pub_receptor, 'tipo', None) if pub_receptor else None
        return es_intercambio_mutuo(tipo_emisor, tipo_receptor)

    def _identificar_roles_trueque(self, trueque):
        """Determina prestador (TALENTO) y receptor_servicio (NECESIDAD) según publicaciones."""
        prestador_id = None
        receptor_servicio_id = None

        pub_emisor = self.publicacion_repository.obtener_por_id(trueque.publicacion_emisor_id) if trueque.publicacion_emisor_id else None
        pub_receptor = self.publicacion_repository.obtener_por_id(trueque.publicacion_receptor_id) if trueque.publicacion_receptor_id else None

        if pub_emisor and es_talento(pub_emisor):
            prestador_id = trueque.emisor_id
        elif pub_emisor and es_necesidad(pub_emisor):
            receptor_servicio_id = trueque.emisor_id

        if pub_receptor and es_talento(pub_receptor):
            prestador_id = trueque.receptor_id
        elif pub_receptor and es_necesidad(pub_receptor):
            receptor_servicio_id = trueque.receptor_id

        if prestador_id and receptor_servicio_id:
            return prestador_id, receptor_servicio_id

        # Fallback sin publicaciones: emisor pierde hora, receptor gana hora.
        return trueque.receptor_id, trueque.emisor_id

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

        # Usar funciones de negocio de Publicacion para validar tipos
        tipo_emisor = "TALENTO" if es_talento(pub_emisor) else "NECESIDAD"
        tipo_receptor = "TALENTO" if es_talento(pub_receptor) else "NECESIDAD"

        if es_necesidad(pub_emisor) and es_necesidad(pub_receptor):
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
        if es_talento(pub_emisor) and es_necesidad(pub_receptor):
            return (
                f"{nombre} te ofrece {pub_emisor.titulo} "
                f"para tu necesidad de {pub_receptor.titulo}."
            )
        if es_necesidad(pub_emisor) and es_talento(pub_receptor):
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

        if not receptor:
            raise BusinessError("Receptor no encontrado.", status_code=404)

        if receptor.id == emisor.id:
            raise BusinessError("No puedes enviarte una propuesta a ti mismo.")

        # Obtener las publicaciones si se proporcionan
        pub_emisor = None
        pub_receptor = None
        
        if publicacion_emisor_id:
            pub_emisor = self.publicacion_repository.obtener_por_id_activa(publicacion_emisor_id)
            if not pub_emisor:
                raise BusinessError("Publicación del emisor no encontrada.", status_code=404)
        
        if publicacion_receptor_id:
            pub_receptor = self.publicacion_repository.obtener_por_id_activa(publicacion_receptor_id)
            if not pub_receptor:
                raise BusinessError("Publicación del receptor no encontrada.", status_code=404)

        self._validar_publicaciones_propuesta(emisor, receptor, pub_emisor, pub_receptor)

        trueque = self.trueque_repository.obtener_o_crear_pendiente(
            emisor_id=emisor.id,
            receptor_id=receptor.id,
            publicacion_emisor_id=getattr(pub_emisor, 'id', None),
            publicacion_receptor_id=getattr(pub_receptor, 'id', None),
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

        # Marcar notificaciones MATCH como leídas para ambos usuarios
        self.notificacion_service.marcar_notificaciones_trueque_leidas_ambos_usuarios(trueque.id, tipos=("MATCH",))

        return trueque  # AcuerdoTruequeDominio — el controlador solo necesita .id

    def responder_propuesta(self, receptor, trueque_id, accion):
        try:
            trueque = self.trueque_repository.obtener_por_receptor(trueque_id, getattr(receptor, 'id', receptor))
        except ObjectDoesNotExist:
            raise BusinessError("Propuesta no encontrada.", status_code=404)

        if not trueque:
            raise BusinessError("Propuesta no encontrada.", status_code=404)

        if accion == "ACEPTAR":
            trueque.estado = "ACEPTADO"
            trueque.codigo_confirmacion = generar_codigo_confirmacion(self.trueque_repository)
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
        """Confirmacion bilateral antes de transferir el saldo de horas."""
        with transaction.atomic():
            try:
                trueque = self.trueque_repository.obtener_bloqueado(trueque_id)
            except ObjectDoesNotExist:
                raise BusinessError("Trueque no encontrado.", status_code=404)

            if not trueque:
                raise BusinessError("Trueque no encontrado.", status_code=404)

            # Autorizar Actores: verificar permisos y medir tiempo de deteccion
            t_inicio = time.perf_counter()
            autorizado, motivo = autorizar_actor_finalizacion(trueque, usuario)
            t_deteccion = (time.perf_counter() - t_inicio) * 1000

            uid = getattr(usuario, 'id', usuario)

            # Registrar intento en el audit log
            registrar_intento_autorizacion(
                usuario_id=uid,
                trueque_id=trueque_id,
                accion='FINALIZAR_TRUEQUE',
                resultado=AUTORIZADO if autorizado else BLOQUEADO,
                motivo=motivo,
                tiempo_deteccion_ms=t_deteccion,
                emisor_id=trueque.emisor_id,
                receptor_id=trueque.receptor_id,
            )

            if not autorizado:
                raise BusinessError(motivo, status_code=403)

            # Usar funcion de negocio para verificar si puede confirmar
            puede_conf, mensaje = puede_confirmar(trueque, usuario)
            if not puede_conf:
                raise BusinessError(mensaje)

            if uid == trueque.emisor_id:
                trueque.emisor_confirmado = True
            else:
                trueque.receptor_confirmado = True

            # Usar función de negocio de AcuerdoTrueque para verificar si ambas partes confirmaron
            if not ambas_partes_confirmaron(trueque):
                self.trueque_repository.guardar(trueque)
                return {
                    "saldo_transferido": False,
                    "impacto_horas": 0,
                    "habilitar_resena": False,
                    "mensaje": "Confirmación registrada. Esperando confirmación de la otra parte.",
                }

            # Pausar las necesidades de ambos usuarios ya que se cumplieron con el trueque
            # Pausar todas las publicaciones de tipo NECESIDAD del emisor
            necesidades_emisor = self.publicacion_repository.listar_por_usuario_y_tipo_activas(trueque.emisor_id, 'NECESIDAD')
            for pub in necesidades_emisor:
                self.publicacion_repository.actualizar_estado(pub.id, trueque.emisor_id, False)
            # Pausar todas las publicaciones de tipo NECESIDAD del receptor
            necesidades_receptor = self.publicacion_repository.listar_por_usuario_y_tipo_activas(trueque.receptor_id, 'NECESIDAD')
            for pub in necesidades_receptor:
                self.publicacion_repository.actualizar_estado(pub.id, trueque.receptor_id, False)

            # Verificar si es intercambio mutuo usando función pura de negocio
            pub_emisor = self.publicacion_repository.obtener_por_id(trueque.publicacion_emisor_id) if trueque.publicacion_emisor_id else None
            pub_receptor = self.publicacion_repository.obtener_por_id(trueque.publicacion_receptor_id) if trueque.publicacion_receptor_id else None
            tipo_emisor = getattr(pub_emisor, 'tipo', None)
            tipo_receptor = getattr(pub_receptor, 'tipo', None)
            if es_intercambio_mutuo(tipo_emisor, tipo_receptor):
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

            prestador_id, receptor_servicio_id = self._identificar_roles_trueque(trueque)

            prestador = self.usuario_repository.obtener_por_id_bloqueado(prestador_id)
            receptor_servicio = self.usuario_repository.obtener_por_id_bloqueado(receptor_servicio_id)

            # Usar función de negocio de Usuario para verificar límite de saldo
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

    def validar_codigo_finalizacion(self, usuario, trueque_id, codigo):
        """Valida el codigo de confirmacion y finaliza el trueque."""
        with transaction.atomic():
            try:
                trueque = self.trueque_repository.obtener_bloqueado(trueque_id)
            except ObjectDoesNotExist:
                raise BusinessError("Trueque no encontrado.", status_code=404)

            if not trueque:
                raise BusinessError("Trueque no encontrado.", status_code=404)

            # Autorizar Actores: solo el receptor puede ingresar el codigo
            t_inicio = time.perf_counter()
            autorizado, motivo = autorizar_actor_codigo(trueque, usuario)
            t_deteccion = (time.perf_counter() - t_inicio) * 1000

            uid = getattr(usuario, 'id', usuario)

            registrar_intento_autorizacion(
                usuario_id=uid,
                trueque_id=trueque_id,
                accion='VALIDAR_CODIGO',
                resultado=AUTORIZADO if autorizado else BLOQUEADO,
                motivo=motivo,
                tiempo_deteccion_ms=t_deteccion,
                emisor_id=trueque.emisor_id,
                receptor_id=trueque.receptor_id,
            )

            if not autorizado:
                raise BusinessError(motivo, status_code=403)

            # Verificar que el codigo sea correcto
            if trueque.codigo_confirmacion != codigo:
                raise BusinessError("Codigo de confirmacion incorrecto.", status_code=400)

            # Marcar ambas partes como confirmadas ya que el código valida el trueque
            trueque.emisor_confirmado = True
            trueque.receptor_confirmado = True

            # Pausar las necesidades de ambos usuarios ya que se cumplieron con el trueque
            # Pausar todas las publicaciones de tipo NECESIDAD del emisor
            necesidades_emisor = self.publicacion_repository.listar_por_usuario_y_tipo_activas(trueque.emisor_id, 'NECESIDAD')
            for pub in necesidades_emisor:
                self.publicacion_repository.actualizar_estado(pub.id, trueque.emisor_id, False)
            # Pausar todas las publicaciones de tipo NECESIDAD del receptor
            necesidades_receptor = self.publicacion_repository.listar_por_usuario_y_tipo_activas(trueque.receptor_id, 'NECESIDAD')
            for pub in necesidades_receptor:
                self.publicacion_repository.actualizar_estado(pub.id, trueque.receptor_id, False)

            # Verificar si es intercambio mutuo usando función pura de negocio
            pub_emisor = self.publicacion_repository.obtener_por_id(trueque.publicacion_emisor_id) if trueque.publicacion_emisor_id else None
            pub_receptor = self.publicacion_repository.obtener_por_id(trueque.publicacion_receptor_id) if trueque.publicacion_receptor_id else None
            tipo_emisor = getattr(pub_emisor, 'tipo', None)
            tipo_receptor = getattr(pub_receptor, 'tipo', None)
            if es_intercambio_mutuo(tipo_emisor, tipo_receptor):
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

            # Para trueques no mutuos, transferir horas
            prestador_id, receptor_servicio_id = self._identificar_roles_trueque(trueque)
            prestador = self.usuario_repository.obtener_por_id_bloqueado(prestador_id)
            receptor_servicio = self.usuario_repository.obtener_por_id_bloqueado(receptor_servicio_id)

            # Transferir horas
            prestador.horas_de_vida += 1
            receptor_servicio.horas_de_vida -= 1
            self.usuario_repository.guardar(prestador)
            self.usuario_repository.guardar(receptor_servicio)

            trueque.estado = "FINALIZADO"
            self.trueque_repository.guardar(trueque)

            return {
                "saldo_transferido": True,
                "impacto_horas": 1 if uid == prestador_id else -1,
                "habilitar_resena": True,
                "mensaje": "Trueque finalizado exitosamente. Sistema de reseñas habilitado.",
            }

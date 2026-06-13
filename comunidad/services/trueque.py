from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from .base import BusinessError, generar_codigo_confirmacion
from ..interfaces import TruequeInterface
from ..repositories import AcuerdoTruequeRepository, UsuarioRepository, PublicacionRepository
from .notificacion import NotificacionService


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
        from ..models import Publicacion
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

        # Marcar todas las notificaciones MATCH de este trueque como leídas para ambos usuarios
        # Esto evita que ambos usuarios sigan viendo la notificación MATCH después de crear una propuesta
        self.notificacion_service.marcar_notificaciones_trueque_leidas_ambos_usuarios(trueque.id, tipos=("MATCH",))
        
        return trueque

    def responder_propuesta(self, receptor, trueque_id, accion):
        try:
            trueque = self.trueque_repository.obtener_por_receptor(trueque_id, receptor)
        except ObjectDoesNotExist:
            raise BusinessError("Propuesta no encontrada.", status_code=404)

        if accion == "ACEPTAR":
            trueque.estado = "EN_CURSO"
            trueque.codigo_confirmacion = generar_codigo_confirmacion()
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

            # Pausar las necesidades de ambos usuarios ya que se cumplieron con el trueque
            from ..models import Publicacion
            # Pausar todas las publicaciones de tipo NECESIDAD del emisor
            necesidades_emisor = Publicacion.objects.filter(usuario=trueque.emisor, tipo='NECESIDAD', esta_activa=True)
            for pub in necesidades_emisor:
                pub.esta_activa = False
                pub.save()
            # Pausar todas las publicaciones de tipo NECESIDAD del receptor
            necesidades_receptor = Publicacion.objects.filter(usuario=trueque.receptor, tipo='NECESIDAD', esta_activa=True)
            for pub in necesidades_receptor:
                pub.esta_activa = False
                pub.save()

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


    def validar_codigo_finalizacion(self, usuario, trueque_id, codigo):
        """Valida el código de confirmación y finaliza el trueque si es correcto."""
        with transaction.atomic():
            try:
                trueque = self.trueque_repository.obtener_bloqueado(trueque_id)
            except ObjectDoesNotExist:
                raise BusinessError("Trueque no encontrado.", status_code=404)

            # Verificar que el usuario es parte del trueque
            if not trueque.participante(usuario):
                raise BusinessError("No eres parte de este trueque.", status_code=403)

            # Verificar que el trueque está en curso
            if not trueque.esta_en_curso():
                raise BusinessError("El trueque debe estar en curso para finalizar.", status_code=400)

            # Verificar que el código sea correcto
            if trueque.codigo_confirmacion != codigo:
                raise BusinessError("Código de confirmación incorrecto.", status_code=400)

            # Verificar que solo el receptor pueda introducir el código
            if usuario == trueque.emisor:
                raise BusinessError("Solo el receptor puede introducir el código del emisor.", status_code=403)

            # Marcar ambas partes como confirmadas ya que el código valida el trueque
            trueque.emisor_confirmado = True
            trueque.receptor_confirmado = True

            # Pausar las necesidades de ambos usuarios ya que se cumplieron con el trueque
            from ..models import Publicacion
            # Pausar todas las publicaciones de tipo NECESIDAD del emisor
            necesidades_emisor = Publicacion.objects.filter(usuario=trueque.emisor, tipo='NECESIDAD', esta_activa=True)
            for pub in necesidades_emisor:
                pub.esta_activa = False
                pub.save()
            # Pausar todas las publicaciones de tipo NECESIDAD del receptor
            necesidades_receptor = Publicacion.objects.filter(usuario=trueque.receptor, tipo='NECESIDAD', esta_activa=True)
            for pub in necesidades_receptor:
                pub.esta_activa = False
                pub.save()

            # Verificar si es intercambio mutuo
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

            # Para trueques no mutuos, transferir horas
            prestador, receptor_servicio = self._identificar_roles_trueque(trueque)
            prestador = self.usuario_repository.obtener_por_id_bloqueado(prestador.id)
            receptor_servicio = self.usuario_repository.obtener_por_id_bloqueado(receptor_servicio.id)

            # Transferir horas
            prestador.horas_de_vida += 1
            receptor_servicio.horas_de_vida -= 1
            self.usuario_repository.guardar(prestador)
            self.usuario_repository.guardar(receptor_servicio)

            trueque.estado = "FINALIZADO"
            self.trueque_repository.guardar(trueque)

            return {
                "saldo_transferido": True,
                "impacto_horas": 1 if usuario == prestador else -1,
                "habilitar_resena": True,
                "mensaje": "Trueque finalizado exitosamente. Sistema de reseñas habilitado.",
            }

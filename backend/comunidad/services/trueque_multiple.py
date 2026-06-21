from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from collections import namedtuple

import logging
from .base import BusinessError, generar_codigo_confirmacion
from ..repositorios_implementacion import TruequeMultipleRepository, UsuarioRepository, PublicacionRepository
from .notificacion import NotificacionService

# Proxy ligero de usuario para el algoritmo de detección de ciclos.
# Evita que el servicio acceda al ORM directamente; se construye
# desde los campos desnormalizados de PublicacionDominio.
_UsuarioProxy = namedtuple(
    '_UsuarioProxy',
    ['id', 'username', 'nombre_real', 'is_active', 'horas_de_vida']
)
from ..negocio.trueque_multiple import (
    esta_expirado,
    todos_aceptaron,
    todos_pares_confirmaron,
    es_participante,
    obtener_rol,
    obtener_pares_del_usuario,
)


class TruequeMultipleService:
    def __init__(self, repository=None, usuario_repository=None, publicacion_repository=None, notificacion_service=None):
        self.repository = repository or TruequeMultipleRepository()
        self.usuario_repository = usuario_repository or UsuarioRepository()
        self.publicacion_repository = publicacion_repository or PublicacionRepository()
        self.notificacion_service = notificacion_service or NotificacionService()
    
    def listar_por_usuario(self, usuario):
        """Lista los trueques múltiples de un usuario."""
        return self.repository.listar_por_usuario(usuario)
    
    def detectar_ciclo_multiple(self, usuario):
        """Detecta si existe un ciclo A→B→C→A donde el usuario es parte."""
        logger = logging.getLogger(__name__)
        logger.info(f"Iniciando detección de ciclos múltiples para usuario {usuario.id} ({usuario.username})")
        ciclos = []
        # Construir mapas en memoria para reducir queries repetidos
        publicaciones = self.publicacion_repository.obtener_todas_activas()

        if not publicaciones:
            return ciclos

        talentos_por_usuario = {}
        necesidades_por_usuario = {}
        necesidad_usuarios_por_titulo = {}
        usuarios_por_id = {}

        for pub in publicaciones:
            uid = pub.usuario_id
            usuario_proxy = _UsuarioProxy(
                id=pub.usuario_id,
                username=pub.usuario_username,
                nombre_real=pub.usuario_nombre_real,
                is_active=pub.usuario_is_active,
                horas_de_vida=pub.usuario_horas_de_vida,
            )
            usuarios_por_id[uid] = usuario_proxy
            if pub.tipo == 'TALENTO':
                talentos_por_usuario.setdefault(uid, []).append(pub)
            else:
                necesidades_por_usuario.setdefault(uid, []).append(pub)
                necesidad_usuarios_por_titulo.setdefault(pub.titulo, []).append((usuario_proxy, pub))

        # Buscar ciclos A->B->C->A para cualquier usuario y filtrar los que incluyan al usuario pasado
        for uid_a, talentos_a in talentos_por_usuario.items():
            usuario_a = usuarios_por_id.get(uid_a)
            necesidades_a = necesidades_por_usuario.get(uid_a, [])
            if not talentos_a or not necesidades_a:
                continue

            for pub_talento_a in talentos_a:
                titulo_a = pub_talento_a.titulo
                candidatos_b = necesidad_usuarios_por_titulo.get(titulo_a, [])
                logger.info("Buscando candidatos B para talento '%s' de usuario %s: %d encontrados", titulo_a, uid_a, len(candidatos_b))
                for usuario_b_obj, pub_nec_b in candidatos_b:
                    if usuario_b_obj.id == uid_a:
                        continue
                    if not usuario_b_obj.is_active:
                        continue
                    if self.repository.usuario_tiene_trueque_multiple_activo(usuario_b_obj):
                        logger.info("Usuario B %s ya tiene trueque múltiple activo, skip", usuario_b_obj.id)
                        continue

                    talentos_b = talentos_por_usuario.get(usuario_b_obj.id, [])
                    for pub_talento_b in talentos_b:
                        titulo_b = pub_talento_b.titulo
                        candidatos_c = necesidad_usuarios_por_titulo.get(titulo_b, [])
                        for usuario_c_obj, pub_nec_c in candidatos_c:
                            if usuario_c_obj.id in (uid_a, usuario_b_obj.id):
                                continue
                            if not usuario_c_obj.is_active:
                                continue
                            if self.repository.usuario_tiene_trueque_multiple_activo(usuario_c_obj):
                                logger.info("Usuario C %s ya tiene trueque múltiple activo, skip", usuario_c_obj.id)
                                continue

                            talentos_c = talentos_por_usuario.get(usuario_c_obj.id, [])
                            # Verificar si alguno de los talentos de C satisface una necesidad de A
                            necesidad_titulos_a = {p.titulo for p in necesidades_a}
                            for pub_talento_c in talentos_c:
                                if pub_talento_c.titulo in necesidad_titulos_a:
                                    # Verificar saldos mínimos
                                    if (usuario_a.horas_de_vida < -10.0 or
                                        usuario_b_obj.horas_de_vida < -10.0 or
                                        usuario_c_obj.horas_de_vida < -10.0):
                                        logger.info("Alguno tiene saldo < -10, skip: %s, %s, %s", usuario_a.id, usuario_b_obj.id, usuario_c_obj.id)
                                        continue

                                    # Buscar publicaciones específicas para cada par
                                    pub_nec_a = next((p for p in necesidades_a if p.titulo == pub_talento_c.titulo), None)

                                    ciclo = {
                                        'emisor1': usuario_a,
                                        'receptor1': usuario_b_obj,
                                        'publicacion_emisor1': pub_talento_a,
                                        'publicacion_receptor1': pub_nec_b,
                                        'emisor2': usuario_b_obj,
                                        'receptor2': usuario_c_obj,
                                        'publicacion_emisor2': pub_talento_b,
                                        'publicacion_receptor2': pub_nec_c,
                                        'emisor3': usuario_c_obj,
                                        'receptor3': usuario_a,
                                        'publicacion_emisor3': pub_talento_c,
                                        'publicacion_receptor3': pub_nec_a,
                                    }

                                    ciclo_key = (
                                        usuario_a.id, usuario_b_obj.id, usuario_c_obj.id,
                                        pub_talento_a.titulo, pub_talento_b.titulo, pub_talento_c.titulo
                                    )
                                    if ciclo_key not in [c.get('key') for c in ciclos]:
                                        ciclo['key'] = ciclo_key
                                        # Solo añadir si el usuario pasado participa en el ciclo
                                        if usuario.id in (usuario_a.id, usuario_b_obj.id, usuario_c_obj.id):
                                            ciclos.append(ciclo)
                                            logger.info(f"Ciclo detectado: {usuario_a.username} -> {usuario_b_obj.username} -> {usuario_c_obj.username}")

        logger.info(f"Total ciclos detectados para usuario {usuario.id}: {len(ciclos)}")
        return ciclos
    
    def crear_propuesta_multiple(self, ciclo, usuario_origen=None):
        """Crea una propuesta de trueque múltiple dado un ciclo detectado.
        Si `usuario_origen` se entrega, se usa como remitente de las notificaciones.
        """
        
        # Validar que ningún participante tenga trueque múltiple activo
        usuarios = [ciclo['emisor1'], ciclo['emisor2'], ciclo['emisor3']]
        for usuario in usuarios:
            if self.repository.usuario_tiene_trueque_multiple_activo(usuario):
                raise BusinessError(f"El usuario {usuario.username} ya tiene un trueque múltiple activo.")
        
        # Validar saldos mínimos
        for usuario in usuarios:
            if usuario.horas_de_vida < -10.0:
                raise BusinessError(f"El usuario {usuario.username} tiene saldo inferior a -10 horas.")
        
        # Calcular fecha de expiración (48 horas)
        expira_el = timezone.now() + timedelta(hours=48)
        
        # Crear el trueque múltiple
        trueque_multiple = self.repository.crear({
            'emisor1': ciclo['emisor1'],
            'receptor1': ciclo['receptor1'],
            'emisor2': ciclo['emisor2'],
            'receptor2': ciclo['receptor2'],
            'emisor3': ciclo['emisor3'],
            'receptor3': ciclo['receptor3'],
            'publicacion_emisor1': ciclo.get('publicacion_emisor1'),
            'publicacion_receptor1': ciclo.get('publicacion_receptor1'),
            'publicacion_emisor2': ciclo.get('publicacion_emisor2'),
            'publicacion_receptor2': ciclo.get('publicacion_receptor2'),
            'publicacion_emisor3': ciclo.get('publicacion_emisor3'),
            'publicacion_receptor3': ciclo.get('publicacion_receptor3'),
            'estado': 'PENDIENTE',
            'expira_el': expira_el,
        })
        
        # Crear notificaciones para los 3 usuarios
        # Construir detalle del match para facilitar la UI
        match_detalle = {
            'key': ciclo.get('key'),
            'pares': [
                {
                    'emisor_id': ciclo['emisor1'].id,
                    'receptor_id': ciclo['receptor1'].id,
                    'publicacion_emisor_id': getattr(ciclo.get('publicacion_emisor1'), 'id', None),
                    'publicacion_receptor_id': getattr(ciclo.get('publicacion_receptor1'), 'id', None),
                },
                {
                    'emisor_id': ciclo['emisor2'].id,
                    'receptor_id': ciclo['receptor2'].id,
                    'publicacion_emisor_id': getattr(ciclo.get('publicacion_emisor2'), 'id', None),
                    'publicacion_receptor_id': getattr(ciclo.get('publicacion_receptor2'), 'id', None),
                },
                {
                    'emisor_id': ciclo['emisor3'].id,
                    'receptor_id': ciclo['receptor3'].id,
                    'publicacion_emisor_id': getattr(ciclo.get('publicacion_emisor3'), 'id', None),
                    'publicacion_receptor_id': getattr(ciclo.get('publicacion_receptor3'), 'id', None),
                },
            ]
        }

        # Mensajes por usuario (personalizados)
        mensajes = {
            ciclo['emisor1'].id: (
                f"¡Trueque Múltiple detectado! Tú, {ciclo['emisor2'].nombre_real} y {ciclo['emisor3'].nombre_real} "
                f"pueden completar un ciclo de intercambios. Acepta para participar."
            ),
            ciclo['emisor2'].id: (
                f"¡Trueque Múltiple detectado! Tú, {ciclo['emisor1'].nombre_real} y {ciclo['emisor3'].nombre_real} "
                f"pueden completar un ciclo de intercambios. Acepta para participar."
            ),
            ciclo['emisor3'].id: (
                f"¡Trueque Múltiple detectado! Tú, {ciclo['emisor1'].nombre_real} y {ciclo['emisor2'].nombre_real} "
                f"pueden completar un ciclo de intercambios. Acepta para participar."
            ),
        }

        remitente = usuario_origen or ciclo['emisor1']

        # Crear notificaciones usando el servicio de notificaciones
        try:
            # emisor1
            self.notificacion_service.crear_notificacion_propuesta(
                destinatario=ciclo['emisor1'],
                remitente=remitente,
                trueque=None,
                publicacion_original=ciclo.get('publicacion_emisor1'),
                mensaje=mensajes[ciclo['emisor1'].id],
                match_detalle={"trueque_multiple": trueque_multiple.id, "key": ciclo.get('key')},
            )
            # emisor2
            self.notificacion_service.crear_notificacion_propuesta(
                destinatario=ciclo['emisor2'],
                remitente=remitente,
                trueque=None,
                publicacion_original=ciclo.get('publicacion_emisor2'),
                mensaje=mensajes[ciclo['emisor2'].id],
                match_detalle={"trueque_multiple": trueque_multiple.id, "key": ciclo.get('key')},
            )
            # emisor3
            self.notificacion_service.crear_notificacion_propuesta(
                destinatario=ciclo['emisor3'],
                remitente=remitente,
                trueque=None,
                publicacion_original=ciclo.get('publicacion_emisor3'),
                mensaje=mensajes[ciclo['emisor3'].id],
                match_detalle={"trueque_multiple": trueque_multiple.id, "key": ciclo.get('key')},
            )
        except Exception:
            # No hacer fallar la creación del trueque si las notificaciones fallan
            logger = logging.getLogger(__name__)
            logger.exception("Error creando notificaciones para trueque múltiple %s", getattr(trueque_multiple, 'id', None))
        
        return trueque_multiple
    
    def aceptar_propuesta_multiple(self, usuario, trueque_id):
        """Usuario acepta participar en el trueque múltiple."""
        logger = logging.getLogger(__name__)
        with transaction.atomic():
            try:
                logger.info("Aceptar propuesta multiple: usuario=%s trueque_id=%s", getattr(usuario, 'id', usuario), trueque_id)
                trueque = self.repository.obtener_bloqueado(trueque_id)
            except ObjectDoesNotExist:
                logger.exception("Trueque múltiple no encontrado: %s", trueque_id)
                raise BusinessError("Trueque múltiple no encontrado.", status_code=404)

            if not trueque:
                raise BusinessError("Trueque múltiple no encontrado.", status_code=404)

            # Verificar que el usuario es parte del trueque
            if not es_participante(trueque, usuario):
                logger.warning("Usuario %s no es participante del trueque %s", getattr(usuario, 'id', usuario), trueque_id)
                raise BusinessError("No eres parte de este trueque múltiple.", status_code=403)

            # Verificar que no esté expirado
            if esta_expirado(trueque):
                logger.info("Trueque %s expirado, marcando EXPIRADO", trueque_id)
                trueque.estado = 'EXPIRADO'
                self.repository.guardar(trueque)
                raise BusinessError("El trueque múltiple ha expirado.", status_code=400)

            # Verificar estado
            if trueque.estado not in ('PENDIENTE', 'ACEPTADO'):
                logger.info("Aceptar solicitud en estado no válido: %s", trueque.estado)
                raise BusinessError("Solo se pueden aceptar trueques múltiples en estado PENDIENTE o ACEPTADO.", status_code=400)

            # Log estado previo
            logger.debug(
                "Antes de aceptar (trueque=%s) usuario1_aceptado=%s usuario2_aceptado=%s usuario3_aceptado=%s",
                trueque_id, trueque.usuario1_aceptado, trueque.usuario2_aceptado, trueque.usuario3_aceptado,
            )

            # Determinar el rol (preferentemente por emisor) y marcar solo la
            # bandera correspondiente.
            rol = obtener_rol(trueque, usuario)
            logger.info("Marcar aceptación para usuario %s en trueque %s como rol %s", getattr(usuario, 'id', usuario), trueque_id, rol)
            if rol == 1:
                trueque.usuario1_aceptado = True
            elif rol == 2:
                trueque.usuario2_aceptado = True
            elif rol == 3:
                trueque.usuario3_aceptado = True
            else:
                logger.error("No se encontró la participación del usuario %s en el trueque %s", getattr(usuario, 'id', usuario), trueque_id)

            # Log: aceptación por participante
            participantes = {trueque.emisor1_id, trueque.receptor1_id, trueque.emisor2_id, trueque.receptor2_id, trueque.emisor3_id, trueque.receptor3_id}
            aceptacion_por_participante = {}
            for pid in participantes:
                acepto = False
                if pid in (trueque.emisor1_id, trueque.receptor1_id):
                    acepto = acepto or trueque.usuario1_aceptado
                if pid in (trueque.emisor2_id, trueque.receptor2_id):
                    acepto = acepto or trueque.usuario2_aceptado
                if pid in (trueque.emisor3_id, trueque.receptor3_id):
                    acepto = acepto or trueque.usuario3_aceptado
                aceptacion_por_participante[pid] = acepto
            logger.debug("Aceptación por participante (trueque=%s): %s", trueque_id, aceptacion_por_participante)

            # Si todos los participantes únicos aceptaron, cambiar estado y generar códigos
            if todos_aceptaron(trueque):
                logger.info("Todos aceptaron trueque %s, generando códigos y marcando ACEPTADO", trueque_id)
                trueque.estado = 'ACEPTADO'
                if not trueque.codigo_par1:
                    trueque.codigo_par1 = generar_codigo_confirmacion()
                if not trueque.codigo_par2:
                    trueque.codigo_par2 = generar_codigo_confirmacion()
                if not trueque.codigo_par3:
                    trueque.codigo_par3 = generar_codigo_confirmacion()

            self.repository.guardar(trueque)

            # Log estado posterior
            logger.debug(
                "Después de aceptar (trueque=%s) usuario1_aceptado=%s usuario2_aceptado=%s usuario3_aceptado=%s estado=%s",
                trueque_id, trueque.usuario1_aceptado, trueque.usuario2_aceptado, trueque.usuario3_aceptado, trueque.estado,
            )

            if todos_aceptaron(trueque):
                return "Todos los usuarios han aceptado. El trueque múltiple está en curso. Usa los códigos para finalizar cada par."

            return "Aceptación registrada. Esperando que los demás usuarios acepten."
    
    def rechazar_propuesta_multiple(self, usuario, trueque_id):
        """Usuario rechaza el trueque múltiple."""
        with transaction.atomic():
            try:
                trueque = self.repository.obtener_bloqueado(trueque_id)
            except ObjectDoesNotExist:
                raise BusinessError("Trueque múltiple no encontrado.", status_code=404)
            
            if not trueque:
                raise BusinessError("Trueque múltiple no encontrado.", status_code=404)

            # Verificar que el usuario es parte del trueque
            if not es_participante(trueque, usuario):
                raise BusinessError("No eres parte de este trueque múltiple.", status_code=403)
            
            # Cambiar estado a rechazado
            trueque.estado = 'RECHAZADO'
            self.repository.guardar(trueque)
            
            return "Trueque múltiple rechazado. El ciclo ha sido cancelado para todos."
    
    def validar_codigo_par(self, usuario, trueque_id, codigo, par=None):
        """Valida el código de un par específico y marca como confirmado."""
        with transaction.atomic():
            try:
                trueque = self.repository.obtener_bloqueado(trueque_id)
            except ObjectDoesNotExist:
                raise BusinessError("Trueque múltiple no encontrado.", status_code=404)
            
            if not trueque:
                raise BusinessError("Trueque múltiple no encontrado.", status_code=404)

            # Verificar que el usuario es parte del trueque
            if not es_participante(trueque, usuario):
                raise BusinessError("No eres parte de este trueque múltiple.", status_code=403)
            
            # Verificar estado
            if trueque.estado not in ('ACEPTADO', 'EN_CURSO'):
                raise BusinessError("El trueque múltiple debe estar aceptado o en curso para validar códigos.", status_code=400)
            
            # Si se especifica el par, usarlo directamente. Si no, identificarlo automáticamente.
            if par is not None:
                pares = [par]
            else:
                # Identificar a qué par pertenece el usuario
                pares = obtener_pares_del_usuario(trueque, usuario)
                if not pares:
                    raise BusinessError("No se pudo identificar el par del usuario.", status_code=400)
            
            # Validar el código correspondiente
            codigo_valido = False
            for par_num in pares:
                if par_num == 1 and trueque.codigo_par1 == codigo:
                    trueque.par1_confirmado = True
                    codigo_valido = True
                elif par_num == 2 and trueque.codigo_par2 == codigo:
                    trueque.par2_confirmado = True
                    codigo_valido = True
                elif par_num == 3 and trueque.codigo_par3 == codigo:
                    trueque.par3_confirmado = True
                    codigo_valido = True
            
            if not codigo_valido:
                raise BusinessError("Código de validación incorrecto.", status_code=400)
            
            # Cambiar estado a EN_CURSO si es la primera confirmación
            if trueque.estado == 'ACEPTADO':
                trueque.estado = 'EN_CURSO'
            
            # Finalizar el trueque si todos los pares confirmaron
            if todos_pares_confirmaron(trueque):
                trueque.estado = 'FINALIZADO'
                self.repository.guardar(trueque)
                
                # Crear notificaciones de reseña para todos los participantes
                try:
                    # Obtener todos los participantes únicos
                    participantes_unicos = set([
                        trueque.emisor1_id, trueque.receptor1_id,
                        trueque.emisor2_id, trueque.receptor2_id,
                        trueque.emisor3_id, trueque.receptor3_id,
                    ])
                    
                    # Para cada par, crear notificaciones cruzadas de reseña
                    pares = [
                        (trueque.emisor1_id, trueque.receptor1_id),
                        (trueque.emisor2_id, trueque.receptor2_id),
                        (trueque.emisor3_id, trueque.receptor3_id),
                    ]
                    
                    for emisor_id, receptor_id in pares:
                        if emisor_id == receptor_id:
                            continue  # Skip si es el mismo usuario
                        emisor = self.usuario_repository.obtener_por_id(emisor_id)
                        receptor = self.usuario_repository.obtener_por_id(receptor_id)
                        
                        if emisor and receptor:
                            # Notificación para que el emisor califique al receptor
                            self.notificacion_service.crear_notificacion_resena(
                                destinatario=emisor,
                                remitente=receptor,
                                trueque_multiple=trueque,
                                mensaje=f"El trueque múltiple ha finalizado. Deja tu reseña para {receptor.nombre_real}."
                            )
                            # Notificación para que el receptor califique al emisor
                            self.notificacion_service.crear_notificacion_resena(
                                destinatario=receptor,
                                remitente=emisor,
                                trueque_multiple=trueque,
                                mensaje=f"El trueque múltiple ha finalizado. Deja tu reseña para {emisor.nombre_real}."
                            )
                except Exception:
                    # No fallar la finalización si las notificaciones fallan
                    logger = logging.getLogger(__name__)
                    logger.exception("Error creando notificaciones de reseña para trueque múltiple %s", trueque_id)
                
                return "Todos los pares han confirmado. El trueque múltiple ha sido finalizado. Ahora puedes dejar reseñas."
            
            self.repository.guardar(trueque)
            return "Código validado. Esperando confirmación de los demás pares."
    
    def finalizar_par(self, usuario, trueque_id):
        """Finaliza un par específico del ciclo (transferencia de horas)."""
        with transaction.atomic():
            try:
                trueque = self.repository.obtener_bloqueado(trueque_id)
            except ObjectDoesNotExist:
                raise BusinessError("Trueque múltiple no encontrado.", status_code=404)
            
            if not trueque:
                raise BusinessError("Trueque múltiple no encontrado.", status_code=404)

            # Verificar que el usuario es parte del trueque
            if not es_participante(trueque, usuario):
                raise BusinessError("No eres parte de este trueque múltiple.", status_code=403)
            
            # Verificar estado
            if trueque.estado != 'EN_CURSO':
                raise BusinessError("El trueque múltiple debe estar en curso para finalizar pares.", status_code=400)
            
            # Identificar a qué par pertenece el usuario como receptor
            pares = obtener_pares_del_usuario(trueque, usuario)
            if not pares:
                raise BusinessError("No se pudo identificar el par del usuario.", status_code=400)
            
            # Finalizar cada par donde el usuario es receptor
            pares_finalizados = []
            for par in pares:
                emisor = None
                receptor = None
                publicacion_receptor = None
                
                if par == 1:
                    emisor = self.usuario_repository.obtener_por_id(trueque.emisor1_id)
                    receptor = self.usuario_repository.obtener_por_id(trueque.receptor1_id)
                    publicacion_receptor = self.publicacion_repository.obtener_por_id(trueque.publicacion_receptor1_id) if trueque.publicacion_receptor1_id else None
                elif par == 2:
                    emisor = self.usuario_repository.obtener_por_id(trueque.emisor2_id)
                    receptor = self.usuario_repository.obtener_por_id(trueque.receptor2_id)
                    publicacion_receptor = self.publicacion_repository.obtener_por_id(trueque.publicacion_receptor2_id) if trueque.publicacion_receptor2_id else None
                elif par == 3:
                    emisor = self.usuario_repository.obtener_por_id(trueque.emisor3_id)
                    receptor = self.usuario_repository.obtener_por_id(trueque.receptor3_id)
                    publicacion_receptor = self.publicacion_repository.obtener_por_id(trueque.publicacion_receptor3_id) if trueque.publicacion_receptor3_id else None
                
                # Verificar que el par esté confirmado
                if par == 1 and not trueque.par1_confirmado:
                    continue
                if par == 2 and not trueque.par2_confirmado:
                    continue
                if par == 3 and not trueque.par3_confirmado:
                    continue
                
                # Verificar que el usuario sea el receptor
                uid = getattr(usuario, 'id', usuario)
                if getattr(receptor, 'id', None) != uid:
                    continue
                
                # Verificar saldo del receptor
                if receptor.horas_de_vida - 1.0 < -10.0:
                    raise BusinessError("El receptor excedería el límite de -10 horas.", status_code=400)
                
                # Transferir horas
                emisor_bloqueado = self.usuario_repository.obtener_por_id_bloqueado(emisor.id)
                receptor_bloqueado = self.usuario_repository.obtener_por_id_bloqueado(receptor.id)
                
                emisor_bloqueado.horas_de_vida += 1.0
                receptor_bloqueado.horas_de_vida -= 1.0
                
                self.usuario_repository.guardar(emisor_bloqueado)
                self.usuario_repository.guardar(receptor_bloqueado)
                
                # Pausar la necesidad del receptor
                if publicacion_receptor:
                    self.publicacion_repository.actualizar_estado(publicacion_receptor.id, receptor.id, False)
                
                pares_finalizados.append(par)
            
            if not pares_finalizados:
                raise BusinessError("No hay pares pendientes de finalización para este usuario.", status_code=400)
            
            # Verificar si todos los pares están finalizados
            if todos_pares_confirmaron(trueque):
                trueque.estado = 'FINALIZADO'
                self.repository.guardar(trueque)
                return "Todos los pares han finalizado. Trueque múltiple completado."
            
            self.repository.guardar(trueque)
            return f"Par(es) {pares_finalizados} finalizado(s). Transferencia de horas completada."

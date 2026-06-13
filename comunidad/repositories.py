from django.db.models import Case, IntegerField, Q, Value, When

from .models import AcuerdoTrueque, AcuerdoTruequeMultiple, NotificacionPropuesta, Publicacion, Resena, ResenaMultiple, SaldoComercial, Usuario, UsuarioAutorizado


class UsuarioAutorizadoRepository:
    def existe_email(self, email, tipo=None):
        queryset = UsuarioAutorizado.objects.filter(email=email)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        return queryset.exists()

    def guardar_email(self, email, tipo="USUARIO"):
        autorizado, creado = UsuarioAutorizado.objects.update_or_create(
            email=email,
            defaults={"tipo": tipo},
        )
        return autorizado, creado


class UsuarioRepository:
    def existe_username(self, username):
        return Usuario.objects.filter(username=username).exists()

    def crear_usuario(self, username, email, password, nombre_real, es_comercio=False):
        return Usuario.objects.create_user(
            username=username,
            email=email,
            password=password,
            nombre_real=nombre_real,
            es_comercio=es_comercio,
        )

    def obtener_por_id(self, usuario_id):
        return Usuario.objects.get(id=usuario_id)

    def obtener_por_id_bloqueado(self, usuario_id):
        return Usuario.objects.select_for_update().get(id=usuario_id)

    def listar_comercios_activos(self):
        return list(Usuario.objects.filter(es_comercio=True, is_active=True))

    def guardar(self, usuario):
        usuario.save()
        return usuario


class PublicacionRepository:
    def crear(self, usuario, datos):
        return Publicacion.objects.create(usuario=usuario, **datos)

    def obtener_por_id(self, publicacion_id):
        return Publicacion.objects.get(id=publicacion_id)

    def obtener_por_id_y_usuario(self, publicacion_id, usuario):
        return Publicacion.objects.get(id=publicacion_id, usuario=usuario)

    def listar_por_usuario(self, usuario, solo_activas=False):
        queryset = Publicacion.objects.filter(usuario=usuario)
        if solo_activas:
            queryset = queryset.filter(esta_activa=True)
        return list(queryset.order_by("-id"))

    def contar_activas_por_tipo(self, usuario, tipo):
        return Publicacion.objects.filter(usuario=usuario, tipo=tipo, esta_activa=True).count()

    def obtener_cartelera(self, categoria=None, urgencias=None):
        queryset = Publicacion.objects.filter(esta_activa=True)

        if categoria:
            queryset = queryset.filter(categoria=categoria)
        if urgencias:
            queryset = queryset.filter(urgencia__in=urgencias)

        return queryset.annotate(
            prioridad_urgencia=Case(
                When(urgencia="CRITICA", then=Value(3)),
                When(urgencia="ALTA", then=Value(2)),
                When(urgencia="NORMAL", then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
        ).order_by("-prioridad_urgencia", "-id")

    def titulos_activos_por_usuario_y_tipo(self, usuario, tipo):
        return list(
            Publicacion.objects.filter(usuario=usuario, tipo=tipo, esta_activa=True)
            .values_list("titulo", flat=True)
            .distinct()
        )

    def categorias_activas_por_usuario_y_tipo(self, usuario, tipo):
        return list(
            Publicacion.objects.filter(usuario=usuario, tipo=tipo, esta_activa=True)
            .values_list("categoria", flat=True)
        )


class AcuerdoTruequeRepository:
    def crear(self, emisor, receptor, publicacion_emisor=None, publicacion_receptor=None):
        return AcuerdoTrueque.objects.create(
            emisor=emisor,
            receptor=receptor,
            publicacion_emisor=publicacion_emisor,
            publicacion_receptor=publicacion_receptor,
            estado="PENDIENTE",
        )

    def obtener_bloqueado(self, trueque_id):
        return AcuerdoTrueque.objects.select_for_update().get(id=trueque_id)

    def obtener_por_receptor(self, trueque_id, receptor):
        return AcuerdoTrueque.objects.get(id=trueque_id, receptor=receptor)

    def obtener_por_participante(self, trueque_id, usuario):
        return AcuerdoTrueque.objects.get(
            Q(id=trueque_id) & (Q(emisor=usuario) | Q(receptor=usuario))
        )

    def listar_por_usuario(self, usuario):
        return AcuerdoTrueque.objects.filter(
            Q(emisor=usuario) | Q(receptor=usuario)
        ).select_related(
            "emisor",
            "receptor",
            "publicacion_emisor",
            "publicacion_receptor",
        )

    def obtener_o_crear_pendiente(self, emisor, receptor, publicacion_emisor=None, publicacion_receptor=None):
        existente = AcuerdoTrueque.objects.filter(
            Q(emisor=emisor, receptor=receptor) | Q(emisor=receptor, receptor=emisor),
            estado="PENDIENTE",
        ).first()
        if existente:
            existente.emisor = emisor
            existente.receptor = receptor
            if publicacion_emisor is not None:
                existente.publicacion_emisor = publicacion_emisor
            if publicacion_receptor is not None:
                existente.publicacion_receptor = publicacion_receptor
            existente.save()
            return existente
        return self.crear(
            emisor=emisor,
            receptor=receptor,
            publicacion_emisor=publicacion_emisor,
            publicacion_receptor=publicacion_receptor,
        )

    def guardar(self, trueque):
        trueque.save()
        return trueque


class ResenaRepository:
    def crear(self, trueque, calificador, calificado, estrellas, comentario):
        return Resena.objects.create(
            trueque=trueque,
            calificador=calificador,
            calificado=calificado,
            estrellas=estrellas,
            comentario=comentario,
        )

    def listar_por_calificado(self, calificado):
        return list(Resena.objects.filter(calificado=calificado))


class SaldoComercialRepository:
    def crear_movimiento(self, comercio, cliente, monto, tipo_movimiento):
        return SaldoComercial.objects.create(
            comercio=comercio,
            cliente=cliente,
            monto_excedente=monto,
            tipo_movimiento=tipo_movimiento,
        )


class NotificacionPropuestaRepository:
    def crear_notificacion(
        self,
        destinatario,
        remitente,
        trueque=None,
        publicacion_original=None,
        mensaje=None,
        tipo="PROPUESTA",
        match_detalle=None,
    ):
        # Si se recibe un trueque_multiple en match_detalle, utilizar ese campo
        trueque_multiple = None
        if match_detalle and isinstance(match_detalle, dict):
            trueque_multiple = match_detalle.get('trueque_multiple')
            # Si llega un id, intentar resolver la instancia
            try:
                if isinstance(trueque_multiple, int):
                    trueque_multiple = AcuerdoTruequeMultiple.objects.get(id=trueque_multiple)
            except Exception:
                trueque_multiple = None

        return NotificacionPropuesta.objects.create(
            destinatario=destinatario,
            remitente=remitente,
            trueque=trueque,
            publicacion_original=publicacion_original,
            mensaje=mensaje,
            match_detalle=match_detalle,
            prioridad=True,
            estado="PENDIENTE",
            tipo=tipo,
            trueque_multiple=trueque_multiple,
        )

    def existe_match_entre(self, usuario_a, usuario_b):
        """Evita duplicar MATCH si ya hay notificación (incl. LEIDA) con trueque PENDIENTE."""
        return NotificacionPropuesta.objects.filter(
            tipo="MATCH",
            trueque__estado="PENDIENTE",
        ).filter(
            Q(destinatario=usuario_a, remitente=usuario_b)
            | Q(destinatario=usuario_b, remitente=usuario_a)
        ).exists()

    def existe_match_pendiente_entre(self, usuario_a, usuario_b):
        return self.existe_match_entre(usuario_a, usuario_b)

    def actualizar_estado_por_trueque(self, trueque, nuevo_estado):
        return NotificacionPropuesta.objects.filter(
            trueque=trueque,
            tipo="PROPUESTA",
        ).update(estado=nuevo_estado)
    
    def obtener_notificaciones_usuario(self, usuario, incluir_leidas=False):
        from .models import NotificacionPropuesta
        queryset = NotificacionPropuesta.objects.filter(destinatario=usuario)
        if not incluir_leidas:
            queryset = queryset.exclude(estado='LEIDA')
        return list(queryset.order_by('-prioridad', '-creada_el'))
    
    def marcar_como_leida(self, notificacion_id, destinatario=None):
        from .models import NotificacionPropuesta
        from django.utils import timezone

        queryset = NotificacionPropuesta.objects.filter(id=notificacion_id)
        if destinatario is not None:
            queryset = queryset.filter(destinatario=destinatario)
        notificacion = queryset.get()
        notificacion.estado = 'LEIDA'
        notificacion.leida_el = timezone.now()
        notificacion.save()
        return notificacion

    def marcar_leidas_por_trueque(self, usuario, trueque_id, tipos=None):
        from .models import NotificacionPropuesta
        from django.utils import timezone

        tipos = tipos or ("MATCH", "PROPUESTA")
        ahora = timezone.now()
        return NotificacionPropuesta.objects.filter(
            destinatario=usuario,
            trueque_id=trueque_id,
            tipo__in=tipos,
        ).exclude(estado="LEIDA").update(estado="LEIDA", leida_el=ahora)
    
    def marcar_leidas_por_trueque_ambos_usuarios(self, trueque_id, tipos=None):
        """Marca todas las notificaciones de un trueque como leídas para ambos usuarios."""
        from .models import NotificacionPropuesta
        from django.utils import timezone

        tipos = tipos or ("MATCH", "PROPUESTA")
        ahora = timezone.now()
        return NotificacionPropuesta.objects.filter(
            trueque_id=trueque_id,
            tipo__in=tipos,
        ).exclude(estado="LEIDA").update(estado="LEIDA", leida_el=ahora)


class MatchmakingRepository:
    def _construir_match_enriquecido(self, usuario, candidato, titulos_necesidades, titulos_talentos):
        mis_talentos = list(
            Publicacion.objects.filter(
                usuario=usuario,
                tipo="TALENTO",
                esta_activa=True,
                titulo__in=titulos_talentos,
            )
        )
        mis_necesidades = list(
            Publicacion.objects.filter(
                usuario=usuario,
                tipo="NECESIDAD",
                esta_activa=True,
                titulo__in=titulos_necesidades,
            )
        )
        talentos_coincidentes = list(
            Publicacion.objects.filter(
                usuario=candidato,
                tipo="TALENTO",
                esta_activa=True,
                titulo__in=titulos_necesidades,
            )
        )
        necesidades_coincidentes = list(
            Publicacion.objects.filter(
                usuario=candidato,
                tipo="NECESIDAD",
                esta_activa=True,
                titulo__in=titulos_talentos,
            )
        )

        publicaciones_sugeridas = []
        for mi_nec in mis_necesidades:
            for su_tal in talentos_coincidentes:
                if mi_nec.titulo == su_tal.titulo:
                    publicaciones_sugeridas.append(
                        {"mi_pub_id": mi_nec.id, "su_pub_id": su_tal.id}
                    )
        for mi_tal in mis_talentos:
            for su_nec in necesidades_coincidentes:
                if mi_tal.titulo == su_nec.titulo:
                    publicaciones_sugeridas.append(
                        {"mi_pub_id": mi_tal.id, "su_pub_id": su_nec.id}
                    )

        return {
            "usuario": candidato,
            "talentos_coincidentes": talentos_coincidentes,
            "necesidades_coincidentes": necesidades_coincidentes,
            "publicaciones_sugeridas": publicaciones_sugeridas,
        }

    def buscar_matches(self, usuario, titulos_necesidades, titulos_talentos):
        if not titulos_necesidades or not titulos_talentos:
            return []

        candidatos = (
            Usuario.objects.filter(
                publicaciones__tipo="TALENTO",
                publicaciones__titulo__in=titulos_necesidades,
                publicaciones__esta_activa=True,
            )
            .filter(
                publicaciones__tipo="NECESIDAD",
                publicaciones__titulo__in=titulos_talentos,
                publicaciones__esta_activa=True,
            )
            .exclude(id=usuario.id)
            .distinct()
        )

        return [
            self._construir_match_enriquecido(
                usuario, candidato, titulos_necesidades, titulos_talentos
            )
            for candidato in candidatos
        ]
    
    def verificar_coincidencia_por_titulo(self, usuario, publicacion_seleccionada):
        """
        Verifica si el usuario tiene publicaciones con el mismo título que la publicación seleccionada.
        Retorna un diccionario con información sobre las coincidencias.
        """
        if not publicacion_seleccionada or not publicacion_seleccionada.titulo:
            return {
                "tiene_coincidencia": False,
                "publicaciones_coincidentes": [],
                "tipo_buscado": None,
                "titulo": None
            }
        
        # Determinar qué tipo de publicación buscamos (el complementario)
        tipo_buscado = "NECESIDAD" if publicacion_seleccionada.tipo == "TALENTO" else "TALENTO"
        
        # Buscar publicaciones del usuario con el mismo título y tipo complementario
        publicaciones_coincidentes = list(
            Publicacion.objects.filter(
                usuario=usuario,
                titulo=publicacion_seleccionada.titulo,
                tipo=tipo_buscado,
                esta_activa=True,
            )
        )
        
        return {
            "tiene_coincidencia": len(publicaciones_coincidentes) > 0,
            "publicaciones_coincidentes": publicaciones_coincidentes,
            "tipo_buscado": tipo_buscado,
            "titulo": publicacion_seleccionada.titulo
        }
    
    def buscar_matches_por_publicacion(self, usuario, publicacion):
        """
        Busca matches complementarios por título de la publicación seleccionada.
        Si es TALENTO, busca usuarios con NECESIDAD del mismo título (y viceversa).
        """
        if not publicacion or not publicacion.titulo:
            return []

        tipo_buscado = "NECESIDAD" if publicacion.tipo == "TALENTO" else "TALENTO"
        tipo_propio = "TALENTO" if publicacion.tipo == "NECESIDAD" else "NECESIDAD"

        candidatos = (
            Usuario.objects.filter(
                publicaciones__tipo=tipo_buscado,
                publicaciones__titulo=publicacion.titulo,
                publicaciones__esta_activa=True,
            )
            .exclude(id=usuario.id)
            .distinct()
        )

        resultados = []
        for candidato in candidatos:
            pubs_complementarias = list(
                Publicacion.objects.filter(
                    usuario=candidato,
                    tipo=tipo_buscado,
                    titulo=publicacion.titulo,
                    esta_activa=True,
                )
            )
            mis_complementarias = list(
                Publicacion.objects.filter(
                    usuario=usuario,
                    tipo=tipo_propio,
                    esta_activa=True,
                )
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
                    )
                )
            else:
                necesidades_coincidentes = pubs_complementarias
                talentos_coincidentes = list(
                    Publicacion.objects.filter(
                        usuario=candidato,
                        tipo="TALENTO",
                        titulo__in=titulos_mis_complementarias,
                        esta_activa=True,
                    )
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
                    usuario, candidato, titulos_necesidades, titulos_talentos
                )
            )

        return resultados


class AcuerdoTruequeMultipleRepository:
    def crear(self, datos):
        return AcuerdoTruequeMultiple.objects.create(**datos)
    
    def obtener_bloqueado(self, trueque_id):
        return AcuerdoTruequeMultiple.objects.select_for_update().get(id=trueque_id)
    
    def obtener_por_participante(self, trueque_id, usuario):
        return AcuerdoTruequeMultiple.objects.get(
            Q(id=trueque_id) & 
            (Q(emisor1=usuario) | Q(receptor1=usuario) | 
             Q(emisor2=usuario) | Q(receptor2=usuario) | 
             Q(emisor3=usuario) | Q(receptor3=usuario))
        )
    
    def listar_por_usuario(self, usuario):
        return AcuerdoTruequeMultiple.objects.filter(
            Q(emisor1=usuario) | Q(receptor1=usuario) | 
            Q(emisor2=usuario) | Q(receptor2=usuario) | 
            Q(emisor3=usuario) | Q(receptor3=usuario)
        ).select_related(
            'emisor1', 'receptor1', 'emisor2', 'receptor2', 'emisor3', 'receptor3'
        )
    
    def usuario_tiene_trueque_multiple_activo(self, usuario):
        return AcuerdoTruequeMultiple.objects.filter(
            Q(emisor1=usuario) | Q(receptor1=usuario) | 
            Q(emisor2=usuario) | Q(receptor2=usuario) | 
            Q(emisor3=usuario) | Q(receptor3=usuario),
            estado__in=['PENDIENTE', 'ACEPTADO', 'EN_CURSO']
        ).exists()
    
    def guardar(self, trueque):
        trueque.save()
        return trueque


class ResenaMultipleRepository:
    def crear(self, trueque_multiple, calificador, calificado, estrellas, comentario):
        return ResenaMultiple.objects.create(
            trueque_multiple=trueque_multiple,
            calificador=calificador,
            calificado=calificado,
            estrellas=estrellas,
            comentario=comentario,
        )
    
    def listar_por_calificado(self, calificado):
        return list(ResenaMultiple.objects.filter(calificado=calificado))
    
    def existe_resena(self, trueque_multiple, calificador, calificado):
        return ResenaMultiple.objects.filter(
            trueque_multiple=trueque_multiple,
            calificador=calificador,
            calificado=calificado
        ).exists()

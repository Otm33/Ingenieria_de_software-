"""
Sprint 2 HU 2: Como usuario, quiero ver el historial detallado de todos mis trueques pasados,
mi saldo disponible, mi balance final de deudas y créditos para gestionar mi participación.
"""


class PerfilHistorialController:
    """Controlador para Sprint 2 HU 2 — Perfil e historial de trueques."""

    def __init__(self, usuario_repository, publicacion_repository, resena_repository, trueque_repository):
        self._usu_repo = usuario_repository
        self._pub_repo = publicacion_repository
        self._resena_repo = resena_repository
        self._trueque_repo = trueque_repository

    def ver_mi_perfil(self, usuario_orm) -> dict:
        publicaciones = self._pub_repo.listar_por_usuario(usuario_orm.id)
        publicaciones_activas = [p for p in publicaciones if p.esta_activa]
        publicaciones_pausadas = [p for p in publicaciones if not p.esta_activa]
        resenas_recibidas = self._resena_repo.listar_por_calificado(usuario_orm.id)
        trueques = self._trueque_repo.listar_por_usuario(usuario_orm.id)
        trueques_enviados = [t for t in trueques if t.emisor_id == usuario_orm.id]
        trueques_recibidos = [t for t in trueques if t.receptor_id == usuario_orm.id]

        nombre = (usuario_orm.nombre_real or "").strip()
        tiene_publicaciones = len(publicaciones) > 0
        es_miembro = bool(nombre and tiene_publicaciones)

        # Serializar manualmente sin usar serializers
        def serializar_usuario(u):
            return {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "nombre_real": u.nombre_real,
                "horas_de_vida": float(u.horas_de_vida),
                "es_comercio": u.es_comercio,
                "saldo_comercial": float(u.saldo_comercial),
                "promedio_estrellas": u.promedio_estrellas,
                "is_staff": u.is_staff,
                "is_superuser": u.is_superuser,
            }

        def serializar_publicacion(p):
            return {
                "id": p.id,
                "usuario_id": p.usuario_id,
                "tipo": p.tipo,
                "titulo": p.titulo,
                "descripcion": p.descripcion,
                "categoria": p.categoria,
                "urgencia": p.urgencia,
                "esta_activa": p.esta_activa,
                "fecha_creacion": p.fecha_creacion.isoformat() if getattr(p, 'fecha_creacion', None) else None,
            }

        def serializar_resena(r):
            calificador = self._usu_repo.obtener_por_id(r.calificador_id)
            return {
                "id": r.id,
                "calificador_id": r.calificador_id,
                "calificador_username": calificador.username if calificador else "",
                "calificador_nombre": calificador.nombre_real if calificador else "",
                "calificado_id": r.calificado_id,
                "estrellas": r.estrellas,
                "comentario": r.comentario,
                "fecha_creacion": r.fecha_creacion.isoformat() if getattr(r, 'fecha_creacion', None) else None,
            }

        resenas_data = [serializar_resena(r) for r in resenas_recibidas]

        return {
            "usuario": serializar_usuario(usuario_orm),
            "promedio_estrellas": usuario_orm.promedio_estrellas,
            "publicaciones": [serializar_publicacion(p) for p in publicaciones],
            "publicaciones_activas": [serializar_publicacion(p) for p in publicaciones_activas],
            "publicaciones_pausadas": [serializar_publicacion(p) for p in publicaciones_pausadas],
            "resenas_recibidas": resenas_data,
            "cantidad_resenas": len(resenas_data),
            "trueques_enviados_count": len(trueques_enviados),
            "trueques_recibidos_count": len(trueques_recibidos),
            "saldo_comercial": float(usuario_orm.saldo_comercial),
            "es_miembro_activo": es_miembro,
            "cantidad_publicaciones_pausadas": len(publicaciones_pausadas),
        }

    def ver_perfil_otro(self, usuario_id: int) -> dict:
        usuario = self._usu_repo.obtener_por_id(usuario_id)
        if not usuario:
            raise ValueError("Usuario no encontrado.")

        publicaciones_activas = self._pub_repo.listar_por_usuario(usuario.id, solo_activas=True)
        resenas_recibidas = self._resena_repo.listar_por_calificado(usuario.id)

        # Serializar manualmente sin usar serializers
        def serializar_usuario(u):
            return {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "nombre_real": u.nombre_real,
                "horas_de_vida": float(u.horas_de_vida),
                "es_comercio": u.es_comercio,
                "saldo_comercial": float(u.saldo_comercial),
                "promedio_estrellas": u.promedio_estrellas,
                "is_staff": u.is_staff,
                "is_superuser": u.is_superuser,
            }

        def serializar_publicacion(p):
            return {
                "id": p.id,
                "usuario_id": p.usuario_id,
                "tipo": p.tipo,
                "titulo": p.titulo,
                "descripcion": p.descripcion,
                "categoria": p.categoria,
                "urgencia": p.urgencia,
                "esta_activa": p.esta_activa,
                "fecha_creacion": p.fecha_creacion.isoformat() if getattr(p, 'fecha_creacion', None) else None,
            }

        def serializar_resena(r):
            calificador = self._usu_repo.obtener_por_id(r.calificador_id)
            return {
                "id": r.id,
                "calificador_id": r.calificador_id,
                "calificador_username": calificador.username if calificador else "",
                "calificador_nombre": calificador.nombre_real if calificador else "",
                "calificado_id": r.calificado_id,
                "estrellas": r.estrellas,
                "comentario": r.comentario,
                "fecha_creacion": r.fecha_creacion.isoformat() if getattr(r, 'fecha_creacion', None) else None,
            }

        pub_data = [serializar_publicacion(p) for p in publicaciones_activas]
        resenas_data = [serializar_resena(r) for r in resenas_recibidas]

        return {
            "usuario": serializar_usuario(usuario),
            "nombre_real": usuario.nombre_real,
            "promedio_estrellas": usuario.promedio_estrellas,
            "publicaciones": pub_data,
            "resenas": resenas_data,
            "cantidad_publicaciones": len(pub_data),
            "cantidad_resenas": len(resenas_data),
        }

    def listar_comunidad(self) -> dict:
        miembros = self._usu_repo.listar_activos()

        directorio = []
        for miembro in miembros:
            publicaciones = self._pub_repo.listar_por_usuario(miembro.id)
            talentos_activos = [
                p for p in publicaciones
                if p.tipo == "TALENTO" and p.esta_activa
            ]
            nombre = (miembro.nombre_real or "").strip()
            es_miembro = bool(nombre and len(publicaciones) > 0)

            directorio.append({
                "id": miembro.id,
                "nombre_real": miembro.nombre_real,
                "username": miembro.username,
                "promedio_estrellas": miembro.promedio_estrellas,
                "talentos_principales": [p.titulo for p in talentos_activos[:3]],
                "cantidad_talentos": len(talentos_activos),
                "es_miembro_activo": es_miembro,
            })

        return {
            "miembros": directorio,
            "cantidad": len(directorio),
        }

    def listar_mis_trueques(self, usuario_orm, request=None) -> dict:
        trueques = self._trueque_repo.listar_por_usuario(usuario_orm.id)

        # Serializar manualmente sin usar serializers para cumplir con el desacoplamiento de DRF.
        # Necesitamos emisor_nombre, receptor_nombre, publicacion_emisor, publicacion_receptor, puede_confirmar.
        trueques_data = []
        for t in trueques:
            # Obtener nombres de emisor y receptor
            emisor = self._usu_repo.obtener_por_id(t.emisor_id)
            receptor = self._usu_repo.obtener_por_id(t.receptor_id)
            
            # Obtener publicaciones si existen
            pub_emisor_data = None
            if t.publicacion_emisor_id:
                pub = self._pub_repo.obtener_por_id(t.publicacion_emisor_id)
                if pub:
                    pub_emisor_data = {
                        "id": pub.id,
                        "usuario": pub.usuario_id,
                        "tipo": pub.tipo,
                        "titulo": pub.titulo,
                        "descripcion": pub.descripcion,
                        "categoria": pub.categoria,
                        "urgencia": pub.urgencia,
                        "esta_activa": pub.esta_activa,
                    }
                    
            pub_receptor_data = None
            if t.publicacion_receptor_id:
                pub = self._pub_repo.obtener_por_id(t.publicacion_receptor_id)
                if pub:
                    pub_receptor_data = {
                        "id": pub.id,
                        "usuario": pub.usuario_id,
                        "tipo": pub.tipo,
                        "titulo": pub.titulo,
                        "descripcion": pub.descripcion,
                        "categoria": pub.categoria,
                        "urgencia": pub.urgencia,
                        "esta_activa": pub.esta_activa,
                    }

            puede_confirmar = False
            if t.estado == "ACEPTADO":
                if usuario_orm.id == t.emisor_id:
                    puede_confirmar = not t.emisor_confirmado
                elif usuario_orm.id == t.receptor_id:
                    puede_confirmar = not t.receptor_confirmado

            trueques_data.append({
                "id": t.id,
                "emisor_id": t.emisor_id,
                "receptor_id": t.receptor_id,
                "emisor_nombre": emisor.nombre_real if emisor else "",
                "receptor_nombre": receptor.nombre_real if receptor else "",
                "publicacion_emisor_id": t.publicacion_emisor_id,
                "publicacion_receptor_id": t.publicacion_receptor_id,
                "publicacion_emisor": pub_emisor_data,
                "publicacion_receptor": pub_receptor_data,
                "estado": t.estado,
                "puede_confirmar": puede_confirmar,
                "fecha_creacion": None,
            })

        return {
            "trueques": trueques_data,
            "cantidad": len(trueques_data),
        }

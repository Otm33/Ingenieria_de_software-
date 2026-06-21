"""
Capa de Presentacion — Controlador del Panel Admin (Sprint 2 HU3).

Traduce requests HTTP a llamadas del AdminPanelService y serializa respuestas.
"""
from ..services.admin_panel import AdminPanelService


class AdminPanelController:
    """Controlador para todas las operaciones del panel de administracion."""

    def __init__(self, service=None):
        self.service = service or AdminPanelService()

    # ── Dashboard ─────────────────────────────────────────────────────────────

    def dashboard(self, request):
        return self.service.obtener_dashboard(request.user)

    # ── Usuarios ──────────────────────────────────────────────────────────────

    def listar_usuarios(self, request):
        busqueda = request.GET.get('q', None)
        usuarios = self.service.listar_usuarios(request.user, busqueda)
        return {
            'usuarios': [self._serializar_usuario(u) for u in usuarios],
            'cantidad': len(usuarios),
        }

    def toggle_usuario(self, request, usuario_id):
        usuario = self.service.toggle_usuario(request.user, usuario_id)
        return {'usuario': self._serializar_usuario(usuario)}

    def cambiar_rol(self, request, usuario_id):
        import json
        body = json.loads(request.body)
        is_staff = body.get('is_staff', False)
        usuario = self.service.cambiar_rol(request.user, usuario_id, is_staff)
        return {'usuario': self._serializar_usuario(usuario)}

    def eliminar_usuario(self, request, usuario_id):
        return self.service.eliminar_usuario(request.user, usuario_id)

    def editar_usuario(self, request, usuario_id):
        import json
        body = json.loads(request.body)
        usuario = self.service.editar_usuario(request.user, usuario_id, body)
        return {'usuario': self._serializar_usuario(usuario)}

    # ── Publicaciones ─────────────────────────────────────────────────────────

    def listar_publicaciones(self, request):
        busqueda = request.GET.get('q', None)
        publicaciones = self.service.listar_publicaciones(request.user, busqueda)
        return {
            'publicaciones': [self._serializar_publicacion(p) for p in publicaciones],
            'cantidad': len(publicaciones),
        }

    def crear_publicacion(self, request):
        import json
        body = json.loads(request.body)
        publicacion = self.service.crear_publicacion_admin(request.user, body)
        return {'publicacion': self._serializar_publicacion(publicacion)}

    def moderar_publicacion(self, request, publicacion_id):
        import json
        body = json.loads(request.body)
        esta_activa = body.get('esta_activa', True)
        publicacion = self.service.moderar_publicacion(request.user, publicacion_id, esta_activa)
        return {'publicacion': self._serializar_publicacion(publicacion)}

    def eliminar_publicacion(self, request, publicacion_id):
        return self.service.eliminar_publicacion(request.user, publicacion_id)

    def editar_publicacion(self, request, publicacion_id):
        import json
        body = json.loads(request.body)
        publicacion = self.service.editar_publicacion(request.user, publicacion_id, body)
        return {'publicacion': self._serializar_publicacion(publicacion)}

    # ── Trueques ──────────────────────────────────────────────────────────────

    def listar_trueques(self, request):
        busqueda = request.GET.get('q', None)
        trueques = self.service.listar_trueques(request.user, busqueda)
        return {
            'trueques': [self._serializar_trueque(t) for t in trueques],
            'cantidad': len(trueques),
        }

    def actualizar_estado_trueque(self, request, trueque_id):
        import json
        body = json.loads(request.body)
        estado = body.get('estado')
        trueque = self.service.actualizar_estado_trueque(request.user, trueque_id, estado)
        return {'trueque': self._serializar_trueque(trueque)}

    def eliminar_trueque(self, request, trueque_id):
        return self.service.eliminar_trueque(request.user, trueque_id)

    # ── Trueques Multiples ────────────────────────────────────────────────────

    def listar_trueques_multiples(self, request):
        busqueda = request.GET.get('q', None)
        trueques = self.service.listar_trueques_multiples(request.user, busqueda)
        return {
            'trueques_multiples': [self._serializar_trueque_multiple(t) for t in trueques],
            'cantidad': len(trueques),
        }

    def actualizar_estado_trueque_multiple(self, request, trueque_id):
        import json
        body = json.loads(request.body)
        estado = body.get('estado')
        trueque = self.service.actualizar_estado_trueque_multiple(request.user, trueque_id, estado)
        return {'trueque_multiple': self._serializar_trueque_multiple(trueque)}

    def eliminar_trueque_multiple(self, request, trueque_id):
        return self.service.eliminar_trueque_multiple(request.user, trueque_id)

    # ── Resenas ───────────────────────────────────────────────────────────────

    def listar_resenas(self, request):
        busqueda = request.GET.get('q', None)
        resenas = self.service.listar_resenas(request.user, busqueda)
        return {
            'resenas': [self._serializar_resena(r) for r in resenas],
            'cantidad': len(resenas),
        }

    def eliminar_resena(self, request, resena_id):
        return self.service.eliminar_resena(request.user, resena_id)

    # ── Resenas Multiples ─────────────────────────────────────────────────────

    def listar_resenas_multiples(self, request):
        busqueda = request.GET.get('q', None)
        resenas = self.service.listar_resenas_multiples(request.user, busqueda)
        return {
            'resenas_multiples': [self._serializar_resena_multiple(r) for r in resenas],
            'cantidad': len(resenas),
        }

    def eliminar_resena_multiple(self, request, resena_id):
        return self.service.eliminar_resena_multiple(request.user, resena_id)

    # ── Saldos ────────────────────────────────────────────────────────────────

    def listar_saldos(self, request):
        busqueda = request.GET.get('q', None)
        saldos = self.service.listar_saldos(request.user, busqueda)
        return {
            'saldos': self._serializar_saldos(saldos),
            'cantidad': len(saldos),
        }

    # ── Serializadores ────────────────────────────────────────────────────────

    def _serializar_usuario(self, u):
        return {
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'nombre_real': u.nombre_real,
            'horas_de_vida': u.horas_de_vida,
            'es_comercio': u.es_comercio,
            'saldo_comercial': float(u.saldo_comercial),
            'is_active': u.is_active,
            'is_staff': u.is_staff,
            'is_superuser': u.is_superuser,
            'promedio_estrellas': u.promedio_estrellas,
            'estado_social': getattr(u, 'estado_social', 'NINGUNO'),
            'date_joined': u.date_joined.isoformat() if getattr(u, 'date_joined', None) else None,
        }

    def _serializar_publicacion(self, p):
        return {
            'id': p.id,
            'usuario_id': p.usuario_id,
            'usuario_username': p.usuario_username,
            'usuario_nombre_real': p.usuario_nombre_real,
            'tipo': p.tipo,
            'titulo': p.titulo,
            'descripcion': p.descripcion,
            'categoria': p.categoria,
            'urgencia': p.urgencia,
            'esta_activa': p.esta_activa,
        }

    def _serializar_trueque(self, t):
        from backend.comunidad.models import Usuario
        emisor_nombre = ''
        receptor_nombre = ''
        try:
            emisor_nombre = Usuario.objects.get(id=t.emisor_id).nombre_real or ''
        except Exception:
            pass
        try:
            receptor_nombre = Usuario.objects.get(id=t.receptor_id).nombre_real or ''
        except Exception:
            pass
        return {
            'id': t.id,
            'emisor_id': t.emisor_id,
            'emisor_nombre': emisor_nombre,
            'receptor_id': t.receptor_id,
            'receptor_nombre': receptor_nombre,
            'estado': t.estado,
            'publicacion_emisor_id': t.publicacion_emisor_id,
            'publicacion_receptor_id': t.publicacion_receptor_id,
            'publicacion_emisor_titulo': getattr(t, 'publicacion_emisor_titulo', None),
            'publicacion_receptor_titulo': getattr(t, 'publicacion_receptor_titulo', None),
            'codigo_confirmacion': t.codigo_confirmacion,
            'emisor_confirmado': t.emisor_confirmado,
            'receptor_confirmado': t.receptor_confirmado,
        }

    def _serializar_trueque_multiple(self, t):
        return {
            'id': t.id,
            'estado': t.estado,
            'emisor1_id': t.emisor1_id,
            'receptor1_id': t.receptor1_id,
            'emisor2_id': t.emisor2_id,
            'receptor2_id': t.receptor2_id,
            'emisor3_id': t.emisor3_id,
            'receptor3_id': t.receptor3_id,
            'usuario1_aceptado': t.usuario1_aceptado,
            'usuario2_aceptado': t.usuario2_aceptado,
            'usuario3_aceptado': t.usuario3_aceptado,
            'par1_confirmado': t.par1_confirmado,
            'par2_confirmado': t.par2_confirmado,
            'par3_confirmado': t.par3_confirmado,
        }

    def _serializar_resena(self, r):
        return {
            'id': r.id,
            'trueque_id': r.trueque_id,
            'calificador_id': r.calificador_id,
            'calificado_id': r.calificado_id,
            'estrellas': r.estrellas,
            'comentario': r.comentario,
        }

    def _serializar_resena_multiple(self, r):
        return {
            'id': r.id,
            'trueque_multiple_id': r.trueque_multiple_id,
            'calificador_id': r.calificador_id,
            'calificado_id': r.calificado_id,
            'estrellas': r.estrellas,
            'comentario': r.comentario,
        }

    def _serializar_saldos(self, saldos):
        result = []
        for s in saldos:
            result.append({
                'id': s.get('id'),
                'comercio_username': s.get('comercio__username', ''),
                'cliente_username': s.get('cliente__username', ''),
                'monto_excedente': float(s.get('monto_excedente', 0)),
                'tipo_movimiento': s.get('tipo_movimiento', ''),
                'fecha': str(s.get('fecha', '')),
                'valor_producto': float(s['valor_producto']) if s.get('valor_producto') else None,
                'monto_recibido': float(s['monto_recibido']) if s.get('monto_recibido') else None,
            })
        return result

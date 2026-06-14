from ..interfaces import MatchmakingInterface
from ..repositories import PublicacionRepository, MatchmakingRepository, NotificacionPropuestaRepository, AcuerdoTruequeRepository
from .trueque import TruequeService


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
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Obteniendo matches para usuario {usuario.id} ({usuario.username})")

        titulos_necesidades = self.publicacion_repository.titulos_activos_por_usuario_y_tipo(
            usuario, "NECESIDAD"
        )
        titulos_talentos = self.publicacion_repository.titulos_activos_por_usuario_y_tipo(
            usuario, "TALENTO"
        )

        logger.info(f"Usuario {usuario.id} - Necesidades activas: {titulos_necesidades}")
        logger.info(f"Usuario {usuario.id} - Talentos activos: {titulos_talentos}")

        self.matches = self.matchmaking_repository.buscar_matches(
            usuario, titulos_necesidades, titulos_talentos
        )

        logger.info(f"Matches encontrados para usuario {usuario.id}: {len(self.matches)}")
        return self.matches

    def verificar_coincidencia_por_titulo(self, usuario, publicacion_id):
        """Verifica si el usuario tiene publicaciones con el mismo título que la publicación seleccionada."""
        try:
            from ..models import Publicacion
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
            from ..models import Publicacion
            publicacion = Publicacion.objects.get(id=publicacion_id, esta_activa=True)
            self.matches = self.matchmaking_repository.buscar_matches_por_publicacion(usuario, publicacion)
            return self.matches
        except Publicacion.DoesNotExist:
            return []

    @staticmethod
    def _construir_match_detalle(match, usuario):
        """Arma las dos parejas del match desde la perspectiva del destinatario."""
        from ..models import Publicacion

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
        from ..models import Publicacion

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
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Iniciando detección de matches para usuario {usuario.id} ({usuario.username})")
        
        matches = self.obtener_matches(usuario)
        logger.info(f"Se encontraron {len(matches)} matches para usuario {usuario.id}")
        
        notificaciones_creadas = []

        for match in matches:
            otro_usuario = match["usuario"]
            logger.info(f"Procesando match con usuario {otro_usuario.id} ({otro_usuario.username})")
            
            if self.notificacion_repository.existe_match_entre(usuario, otro_usuario):
                logger.info(f"Ya existe un match entre {usuario.id} y {otro_usuario.id}, se omite")
                continue

            pub_emisor, pub_receptor = self._resolver_publicaciones_match_completo(match, usuario)

            if not pub_emisor:
                sugerencia = match["publicaciones_sugeridas"][0] if match["publicaciones_sugeridas"] else {}
                if sugerencia:
                    from ..models import Publicacion

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
            logger.info(f"Creando notificación MATCH para {usuario.id}: {mensaje_para_usuario}")
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
            logger.info(f"Creando notificación MATCH para {otro_usuario.id}: {mensaje_para_match}")
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

        logger.info(f"Detección de matches completada para usuario {usuario.id}. Notificaciones creadas: {len(notificaciones_creadas)}")
        return notificaciones_creadas

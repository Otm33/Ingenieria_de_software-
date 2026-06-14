from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class UsuarioDominio:
    """HU2: Perfil del usuario con balance de Horas de Vida y reputación."""
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    nombre_real: str = ""
    horas_de_vida: float = 0.0
    es_comercio: bool = False
    saldo_comercial: float = 0.0
    is_active: bool = True

    def puede_publicar(self, tipo_publicacion: str, conteo_actual: int) -> tuple[bool, str]:
        if self.tiene_saldo_critico():
            return False, "Saldo crítico inferior a -10 horas. No puedes publicar."

        if tipo_publicacion == 'TALENTO' and conteo_actual >= 5:
            return False, "No puedes tener más de 5 talentos activos publicados simultáneamente."

        if tipo_publicacion == 'NECESIDAD' and conteo_actual >= 3:
            return False, "No puedes tener más de 3 necesidades activas simultáneamente."

        return True, "Puede publicar"

    def tiene_saldo_critico(self) -> bool:
        """HU2: Saldo inferior a -10 horas bloquea publicar y modificar."""
        return self.horas_de_vida < -10.0

    def puede_modificar_publicaciones(self) -> bool:
        return not self.tiene_saldo_critico()

    def es_comercio_activo(self) -> bool:
        """HU5: Solo comercios activos pueden emitir vuelto."""
        return self.es_comercio and self.is_active

    def puede_emitir_vuelto_comercial(self, monto: float) -> tuple[bool, str]:
        if not self.es_comercio_activo():
            return False, "Solo los comercios activos pueden emitir vuelto."
        if self.saldo_comercial < monto:
            return False, "Saldo comercial insuficiente para emitir vuelto."
        return True, "Puede emitir vuelto"

    def puede_pagar_con_saldo(self, monto: float) -> tuple[bool, str]:
        if self.es_comercio:
            return False, "Los comercios no pueden pagar con saldo comercial."
        if self.saldo_comercial < monto:
            return False, "Saldo comercial insuficiente."
        return True, "Puede pagar con saldo"

    def es_miembro_activo(self, tiene_publicaciones: bool) -> bool:
        """HU2: Miembro activo si tiene nombre real y al menos una publicación."""
        nombre = (self.nombre_real or "").strip()
        return bool(nombre and tiene_publicaciones)


@dataclass
class PublicacionDominio:
    """HU2/HU3: Catálogo de talentos y necesidades."""
    id: Optional[int] = None
    usuario_id: int = 0
    tipo: str = "TALENTO"
    titulo: str = ""
    descripcion: str = ""
    categoria: str = ""
    urgencia: str = "NORMAL"
    esta_activa: bool = True

    def es_talento(self) -> bool:
        return self.tipo == 'TALENTO'

    def es_necesidad(self) -> bool:
        return self.tipo == 'NECESIDAD'

    def es_urgente(self) -> bool:
        """HU3: Urgencia Alta o Crítica."""
        return self.urgencia in ['ALTA', 'CRITICA']

    def es_critica(self) -> bool:
        return self.urgencia == 'CRITICA'

    def validar_reglas_negocio(
        self,
        usuario: UsuarioDominio,
        conteo_actual: int,
        es_nueva: bool = True,
    ) -> tuple[bool, str]:
        if not usuario.puede_modificar_publicaciones():
            return False, "Saldo crítico inferior a -10 horas. Operación bloqueada."

        if self.es_talento() and self.urgencia != "NORMAL":
            return False, "Los talentos solo pueden tener urgencia Normal."

        if es_nueva and self.esta_activa:
            puede, msj = usuario.puede_publicar(self.tipo, conteo_actual)
            if not puede:
                return False, msj

        return True, "Validación exitosa"


@dataclass
class AcuerdoTruequeDominio:
    """HU4: Propuesta de trueque entre dos usuarios."""
    id: Optional[int] = None
    emisor_id: int = 0
    receptor_id: int = 0
    estado: str = "PENDIENTE"
    publicacion_emisor_id: Optional[int] = None
    publicacion_receptor_id: Optional[int] = None
    emisor_confirmado: bool = False
    receptor_confirmado: bool = False
    codigo_confirmacion: Optional[str] = None

    def esta_pendiente(self) -> bool:
        return self.estado == 'PENDIENTE'

    def esta_aceptado(self) -> bool:
        return self.estado == 'ACEPTADO'

    def esta_en_curso(self) -> bool:
        return self.estado == 'EN_CURSO'

    def esta_finalizado(self) -> bool:
        return self.estado == 'FINALIZADO'

    def ambas_partes_confirmaron(self) -> bool:
        """HU4: Ambas partes confirmaron la finalización."""
        return self.emisor_confirmado and self.receptor_confirmado

    def puede_confirmar(self, usuario_id: int) -> tuple[bool, str]:
        """HU4: Verifica si un usuario puede confirmar la finalización."""
        if not self.esta_en_curso():
            return False, "Solo se pueden confirmar trueques en curso."
        if usuario_id in (self.emisor_id, self.receptor_id):
            return True, "Puede confirmar"
        return False, "Usuario no es parte del trueque."

    def es_participante(self, usuario_id: int) -> bool:
        return usuario_id in (self.emisor_id, self.receptor_id)

    def contraparte_id(self, usuario_id: int) -> Optional[int]:
        if usuario_id == self.emisor_id:
            return self.receptor_id
        if usuario_id == self.receptor_id:
            return self.emisor_id
        return None


@dataclass
class ResenaDominio:
    """HU4: Calificación post-trueque."""
    id: Optional[int] = None
    trueque_id: int = 0
    calificador_id: int = 0
    calificado_id: int = 0
    estrellas: int = 5
    comentario: str = ""

    def calificacion_valida(self) -> bool:
        return 1 <= self.estrellas <= 5

    def comentario_valido(self) -> tuple[bool, str]:
        if not self.comentario or not self.comentario.strip():
            return False, "El comentario no puede estar vacío."
        if len(self.comentario) > 500:
            return False, "El comentario no puede exceder 500 caracteres."
        return True, "Comentario válido"

    def validar(self) -> tuple[bool, str]:
        if not self.calificacion_valida():
            return False, "La calificación debe estar entre 1 y 5 estrellas."
        valido, mensaje = self.comentario_valido()
        if not valido:
            return False, mensaje
        return True, "Reseña válida"

    def es_positiva(self) -> bool:
        return self.estrellas >= 4

    def es_negativa(self) -> bool:
        return self.estrellas <= 2


@dataclass
class NotificacionDominio:
    """Notificación de propuesta o match."""
    id: Optional[int] = None
    tipo: str = "PROPUESTA"
    destinatario_id: int = 0
    remitente_id: int = 0
    trueque_id: Optional[int] = None
    trueque_multiple_id: Optional[int] = None
    publicacion_original_id: Optional[int] = None
    mensaje: str = ""
    estado: str = "PENDIENTE"

    def esta_leida(self) -> bool:
        return self.estado == 'LEIDA'

    def es_de_tipo_match(self) -> bool:
        return self.tipo == 'MATCH'

    def es_de_tipo_propuesta(self) -> bool:
        return self.tipo == 'PROPUESTA'


@dataclass
class AcuerdoTruequeMultipleDominio:
    """HU Trueque Múltiple: ciclo A→B→C→A entre 3 usuarios."""
    id: Optional[int] = None
    estado: str = "PENDIENTE"
    emisor1_id: int = 0
    receptor1_id: int = 0
    emisor2_id: int = 0
    receptor2_id: int = 0
    emisor3_id: int = 0
    receptor3_id: int = 0
    usuario1_aceptado: bool = False
    usuario2_aceptado: bool = False
    usuario3_aceptado: bool = False
    par1_confirmado: bool = False
    par2_confirmado: bool = False
    par3_confirmado: bool = False

    def todos_aceptaron(self) -> bool:
        # Comprobar aceptación por emisores únicos del ciclo
        emisor_map = {
            1: self.emisor1_id,
            2: self.emisor2_id,
            3: self.emisor3_id,
        }

        unique_emis = set(emisor_map.values())
        for pid in unique_emis:
            acepto = False
            for idx, em_pid in emisor_map.items():
                if em_pid == pid:
                    if idx == 1 and self.usuario1_aceptado:
                        acepto = True
                        break
                    if idx == 2 and self.usuario2_aceptado:
                        acepto = True
                        break
                    if idx == 3 and self.usuario3_aceptado:
                        acepto = True
                        break
            if not acepto:
                return False
        return True

    def todos_pares_confirmaron(self) -> bool:
        return self.par1_confirmado and self.par2_confirmado and self.par3_confirmado

    def esta_finalizado(self) -> bool:
        return self.estado == 'FINALIZADO'

    def es_participante(self, usuario_id: int) -> bool:
        return usuario_id in (
            self.emisor1_id, self.receptor1_id,
            self.emisor2_id, self.receptor2_id,
            self.emisor3_id, self.receptor3_id,
        )

    def obtener_rol(self, usuario_id: int) -> Optional[int]:
        """Retorna el número de par (1, 2 o 3) en el que participa el usuario."""
        # Preferir la correspondencia por emisor (cada emisor representa un
        # participante único del ciclo). Si no coincide, usar receptor como
        # fallback por compatibilidad.
        if usuario_id == self.emisor1_id:
            return 1
        if usuario_id == self.emisor2_id:
            return 2
        if usuario_id == self.emisor3_id:
            return 3
        if usuario_id == self.receptor1_id:
            return 1
        if usuario_id == self.receptor2_id:
            return 2
        if usuario_id == self.receptor3_id:
            return 3
        return None

from dataclasses import dataclass
from typing import Optional


# ── HU Registro ─────────────────────────────────────────────────────────────
@dataclass
class RegistroUsuarioRequest:
    """DTO para registrar un nuevo usuario."""
    username: str
    email: str
    password: str
    nombre_real: str
    es_comercio: bool = False


# ── HU Crear Publicación ─────────────────────────────────────────────────────
@dataclass
class CrearPublicacionRequest:
    """DTO para crear una nueva publicación (talento o necesidad)."""
    tipo: str
    titulo: str
    descripcion: str
    categoria: str
    urgencia: str = "NORMAL"
    esta_activa: bool = True


# ── HU Gestión Publicaciones ─────────────────────────────────────────────────
@dataclass
class ActualizarPublicacionRequest:
    """DTO para activar/pausar una publicación."""
    esta_activa: bool


# ── HU Autenticación ─────────────────────────────────────────────────────────
@dataclass
class LoginRequest:
    """DTO para iniciar sesión."""
    username: str
    password: str


# ── HU Proponer Trueque ──────────────────────────────────────────────────────
@dataclass
class PropuestaRequest:
    """DTO para crear una propuesta de trueque."""
    receptor_id: int
    publicacion_emisor_id: Optional[int] = None
    publicacion_receptor_id: Optional[int] = None


@dataclass
class ResponderPropuestaRequest:
    """DTO para aceptar o rechazar una propuesta de trueque."""
    accion: str  # "ACEPTAR" | "RECHAZAR"


# ── HU Finalizar Trueque ─────────────────────────────────────────────────────
@dataclass
class ValidarCodigoRequest:
    """DTO para validar el código de confirmación de finalización."""
    codigo: str


# ── HU Dejar Reseña ──────────────────────────────────────────────────────────
@dataclass
class ResenaRequest:
    """DTO para registrar una reseña de un trueque simple."""
    trueque_id: int
    calificado_id: int
    estrellas: int
    comentario: str


@dataclass
class ResenaMultipleRequest:
    """DTO para registrar una reseña de un trueque múltiple."""
    trueque_multiple_id: int
    calificado_id: int
    estrellas: int
    comentario: str


# ── HU Saldo Comercial ───────────────────────────────────────────────────────
@dataclass
class EmitirVueltoRequest:
    """DTO para que un comercio emita vuelto en saldo comercial a un cliente."""
    cliente_id: int
    valor_producto: float | None = None
    monto_recibido: float | None = None
    monto_excedente: float | None = None


@dataclass
class PagarConSaldoRequest:
    """DTO para que un cliente pague con saldo comercial en un comercio."""
    comercio_id: int
    monto: float


# ── HU Matchmaking ───────────────────────────────────────────────────────────
@dataclass
class MatchmakingRequest:
    """DTO para buscar matches (publicación_id es opcional)."""
    publicacion_id: Optional[int] = None
    accion: Optional[str] = None  # "verificar_coincidencia" | None

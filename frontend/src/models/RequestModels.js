// ============================================================
// Request Models (DTOs) — Frontend
// La Vista crea estas clases y el backend valida nuevamente.
// ============================================================

// ── HU Registro ──────────────────────────────────────────────
export class RegistroUsuarioRequest {
    constructor({ username, email, password, nombre_real, es_comercio = false }) {
        this.username = username;
        this.email = email;
        this.password = password;
        this.nombre_real = nombre_real;
        this.es_comercio = es_comercio;
    }

    validar() {
        if (!this.email || !this.email.includes("@")) {
            throw new Error("El correo electrónico no es válido.");
        }
        if (!this.password || this.password.length < 6) {
            throw new Error("La contraseña debe tener al menos 6 caracteres.");
        }
        if (!this.nombre_real || this.nombre_real.trim().length < 2) {
            throw new Error("El nombre real debe tener al menos 2 caracteres.");
        }
        return true;
    }
}

// ── HU Crear Publicación ─────────────────────────────────────
export class CrearPublicacionRequest {
    constructor({ tipo, titulo, descripcion, categoria, urgencia = "NORMAL" }) {
        this.tipo = tipo;
        this.titulo = titulo;
        this.descripcion = descripcion;
        this.categoria = categoria;
        this.urgencia = urgencia;
        this.esta_activa = true;
    }

    validar() {
        if (!this.titulo || this.titulo.length < 5) {
            throw new Error("El título debe tener al menos 5 caracteres.");
        }
        if (!this.descripcion || this.descripcion.trim().length < 10) {
            throw new Error("La descripción debe tener al menos 10 caracteres.");
        }
        if (this.tipo === 'TALENTO' && this.urgencia !== "NORMAL") {
            throw new Error("Los talentos solo pueden tener urgencia Normal.");
        }
        return true;
    }
}

// ── HU Gestión Publicaciones ─────────────────────────────────
export class ActualizarPublicacionRequest {
    constructor({ esta_activa }) {
        this.esta_activa = esta_activa;
    }

    validar() {
        if (typeof this.esta_activa !== 'boolean') {
            throw new Error("El campo 'esta_activa' debe ser verdadero o falso.");
        }
        return true;
    }
}

// ── HU Autenticación ─────────────────────────────────────────
export class LoginRequest {
    constructor({ username, password }) {
        this.username = username;
        this.password = password;
    }

    validar() {
        if (!this.username || this.username.trim().length === 0) {
            throw new Error("El nombre de usuario es obligatorio.");
        }
        if (!this.password || this.password.length === 0) {
            throw new Error("La contraseña es obligatoria.");
        }
        return true;
    }
}

// ── HU Proponer Trueque ──────────────────────────────────────
export class PropuestaRequest {
    constructor({ receptor_id, publicacion_emisor_id = null, publicacion_receptor_id = null }) {
        this.receptor_id = receptor_id;
        this.publicacion_emisor_id = publicacion_emisor_id;
        this.publicacion_receptor_id = publicacion_receptor_id;
    }

    validar() {
        if (!this.receptor_id) {
            throw new Error("Debes seleccionar un usuario receptor.");
        }
        return true;
    }
}

export class ResponderPropuestaRequest {
    constructor({ accion }) {
        this.accion = accion; // "ACEPTAR" | "RECHAZAR"
    }

    validar() {
        if (!['ACEPTAR', 'RECHAZAR'].includes(this.accion)) {
            throw new Error("Acción inválida. Debe ser ACEPTAR o RECHAZAR.");
        }
        return true;
    }
}

// ── HU Finalizar Trueque ─────────────────────────────────────
export class ValidarCodigoRequest {
    constructor({ codigo }) {
        this.codigo = codigo;
    }

    validar() {
        if (!this.codigo || this.codigo.trim().length === 0) {
            throw new Error("El código de confirmación es obligatorio.");
        }
        return true;
    }
}

// ── HU Dejar Reseña ──────────────────────────────────────────
export class ResenaRequest {
    constructor({ trueque_id, calificado_id, estrellas, comentario }) {
        this.trueque_id = trueque_id;
        this.calificado_id = calificado_id;
        this.estrellas = estrellas;
        this.comentario = comentario;
    }

    validar() {
        if (!this.estrellas || this.estrellas < 1 || this.estrellas > 5) {
            throw new Error("La calificación debe ser entre 1 y 5 estrellas.");
        }
        if (!this.comentario || this.comentario.trim().length === 0) {
            throw new Error("El comentario no puede estar vacío.");
        }
        if (this.comentario.length > 500) {
            throw new Error("El comentario no puede exceder 500 caracteres.");
        }
        return true;
    }
}

export class ResenaMultipleRequest {
    constructor({ trueque_multiple_id, calificado_id, estrellas, comentario }) {
        this.trueque_multiple_id = trueque_multiple_id;
        this.calificado_id = calificado_id;
        this.estrellas = estrellas;
        this.comentario = comentario;
    }

    validar() {
        if (!this.estrellas || this.estrellas < 1 || this.estrellas > 5) {
            throw new Error("La calificación debe ser entre 1 y 5 estrellas.");
        }
        if (!this.comentario || this.comentario.trim().length === 0) {
            throw new Error("El comentario no puede estar vacío.");
        }
        if (this.comentario.length > 500) {
            throw new Error("El comentario no puede exceder 500 caracteres.");
        }
        return true;
    }
}

// ── HU Saldo Comercial ───────────────────────────────────────
export class EmitirVueltoRequest {
    constructor({ cliente_id, valor_producto = null, monto_recibido = null, monto_excedente = null }) {
        this.cliente_id = cliente_id;
        this.valor_producto = valor_producto;
        this.monto_recibido = monto_recibido;
        this.monto_excedente = monto_excedente;
    }

    validar() {
        if (!this.cliente_id) {
            throw new Error("El ID del cliente es obligatorio.");
        }
        if (!this.monto_excedente || this.monto_excedente <= 0) {
            throw new Error("El monto excedente debe ser mayor a cero.");
        }
        return true;
    }
}

export class PagarConSaldoRequest {
    constructor({ comercio_id, monto }) {
        this.comercio_id = comercio_id;
        this.monto = monto;
    }

    validar() {
        if (!this.comercio_id) {
            throw new Error("Debes seleccionar un comercio.");
        }
        if (!this.monto || this.monto <= 0) {
            throw new Error("El monto debe ser mayor a cero.");
        }
        return true;
    }
}

// ── HU Matchmaking ───────────────────────────────────────────────────────
export class MatchmakingRequest {
    constructor({ publicacion_id = null, accion = null }) {
        this.publicacion_id = publicacion_id;
        this.accion = accion; // 'verificar_coincidencia' | null
    }

    validar() {
        // publicacion_id es opcional
        if (this.accion && !['verificar_coincidencia'].includes(this.accion)) {
            throw new Error('Acción de matchmaking inválida.');
        }
        return true;
    }
}

// ── HU Trueque Múltiple ────────────────────────────────────────────────
export class PropuestaMultipleRequest {
    constructor({ participantes = [], publicaciones = [] }) {
        this.participantes = participantes; // array de user ids
        this.publicaciones = publicaciones; // array de publicacion ids en mismo orden
    }

    validar() {
        if (!Array.isArray(this.participantes) || this.participantes.length < 3) {
            throw new Error('Se requieren al menos 3 participantes para un trueque múltiple.');
        }
        if (!Array.isArray(this.publicaciones) || this.publicaciones.length !== this.participantes.length) {
            throw new Error('Debe proveer una publicación por cada participante.');
        }
        return true;
    }
}

export class ValidarCodigoParRequest {
    constructor({ codigo, par }) {
        this.codigo = codigo;
        this.par = par; // número del par (1,2,3)
    }

    validar() {
        if (!this.codigo || this.codigo.trim().length === 0) {
            throw new Error('El código de confirmación es obligatorio.');
        }
        if (![1,2,3].includes(this.par)) {
            throw new Error('Par inválido. Debe ser 1, 2 o 3.');
        }
        return true;
    }
}

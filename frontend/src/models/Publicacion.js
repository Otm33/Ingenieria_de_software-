export default class Publicacion {
  // CAMBIO MODELO: normaliza cada publicacion recibida desde la BD via API Django.
  constructor({
    id = null,
    usuario = null,
    usuario_nombre_real = '',
    usuario_estrellas = 5,
    tipo = '',
    titulo = '',
    descripcion = '',
    categoria = '',
    urgencia = 'NORMAL',
    esta_activa = true,
  } = {}) {
    this.id = id
    this.usuario = usuario
    this.usuarioNombreReal = usuario_nombre_real
    this.usuarioEstrellas = Number(usuario_estrellas || 5)
    this.tipo = tipo
    this.titulo = titulo
    this.descripcion = descripcion
    this.categoria = categoria
    this.urgencia = urgencia
    this.estaActiva = Boolean(esta_activa)
  }
}

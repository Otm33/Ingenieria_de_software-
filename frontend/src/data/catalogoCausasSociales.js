/**
 * Whitelist curada de causas sociales: subset del catálogo de cartelera (catalogoServicios.js).
 * Solo necesidades de personas vulnerables (cuidado, salud, educación inclusiva, movilidad).
 * Mantener sincronizado con backend/comunidad/catalogo_causas_sociales.py
 */
import { TITULOS_POR_CATEGORIA } from './catalogoServicios.js'

/** Títulos de cartelera permitidos para solicitudes de Impacto Social. */
export const TITULOS_CAUSA_SOCIAL_PERMITIDOS = [
  // Cuidado de la Salud, Bienestar y Terapias
  'Cuidado de abuelos',
  'Acompañamiento médico',
  'Cuidado de pacientes',
  'Enfermería a domicilio',
  'Inyectología',
  'Curación de heridas',
  'Control de tensión',
  'Fisioterapia en casa',
  'Rehabilitación física',
  'Terapia ocupacional',
  'Terapia de lenguaje',
  'Estimulación temprana',
  'Gimnasia prenatal',
  'Terapia de duelo',
  'Orientación familiar',
  'Psicoterapia clínica',
  // Educación, Asesoría y Tutorías
  'Apoyo escolar primaria',
  'Apoyo bachillerato',
  'Redacción en español',
  'Técnicas de estudio',
  // Automotriz, Transporte y Logística
  'Conductor de reemplazo',
  'Chófer privado',
  'Transporte escolar',
]

const _permitidos = new Set(TITULOS_CAUSA_SOCIAL_PERMITIDOS)

export const TITULOS_CAUSA_SOCIAL = Object.fromEntries(
  Object.entries(TITULOS_POR_CATEGORIA)
    .map(([categoria, titulos]) => [
      categoria,
      titulos.filter((titulo) => _permitidos.has(titulo)),
    ])
    .filter(([, titulos]) => titulos.length > 0),
)

export const CATEGORIAS_CAUSA_SOCIAL = Object.keys(TITULOS_CAUSA_SOCIAL)

export const titulosCausaSocialPorCategoria = (categoria) =>
  TITULOS_CAUSA_SOCIAL[categoria] || []

export const esTituloCausaSocialPermitido = (titulo) =>
  _permitidos.has(titulo)

export const esCategoriaCausaSocialPermitida = (categoria) =>
  CATEGORIAS_CAUSA_SOCIAL.includes(categoria)

export const categoriaParaTitulo = (titulo) => {
  for (const [categoria, titulos] of Object.entries(TITULOS_CAUSA_SOCIAL)) {
    if (titulos.includes(titulo)) return categoria
  }
  return null
}

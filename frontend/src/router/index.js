/**
 * Configuración de Vue Router — Navegación SPA.
 *
 * Capa: router/ (Presentación del frontend)
 *
 * Define las rutas de la aplicación. Actualmente la app funciona como
 * una single-page sin navegación por URL: todas las rutas redirigen a '/'.
 *
 * La navegación entre secciones (Cartelera, Perfil, Comunidad, etc.) se
 * maneja mediante el componente App.vue con pestañas reactivas, no con
 * rutas de Vue Router. Esto simplifica el estado pero podría ampliarse
 * a rutas reales en el futuro (ej: /cartelera, /perfil/:id).
 *
 * Usa createWebHistory (HTML5 History API) para URLs limpias sin '#'.
 */
import { createRouter, createWebHistory } from 'vue-router'

// CAMBIO VISTA: la aplicacion queda como una sola pagina real en /.
const routes = [
  {
    path: '/',
    component: { template: '<span />' },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router

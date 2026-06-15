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

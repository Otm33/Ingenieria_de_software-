import { createRouter, createWebHistory } from 'vue-router'

// CORREGIDO: Ahora los nombres apuntan exactamente a tus archivos reales
import Cartelera from '../views/Cartelera.vue' 
import Register from '../views/Register.vue'
import AdminCSV from '../views/AdminCSV.vue'

const routes = [
  {
    path: '/',
    name: 'cartelera',
    component: Cartelera
  },
  {
    path: '/register',
    name: 'register',
    component: Register
  },
  {
    path: '/admin-csv',
    name: 'admin-csv',
    component: AdminCSV
  }

]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router

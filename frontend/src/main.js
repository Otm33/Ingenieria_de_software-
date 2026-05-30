import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './styles.css'

import UserService from './models/UserService.js'
import UserController from './controllers/UserController.js'

// CAMBIO MVC/POO: se instancia el modelo/servicio con la API Django que escribe en la BD.
const userService = new UserService('/api/')
// CAMBIO MVC/POO: se instancia el controlador y se inyecta en las vistas Vue.
const userController = new UserController(userService)

const app = createApp(App)
// CAMBIO VISTA: los componentes consumen el controlador, no la BD ni fetch directamente.
app.provide('userController', userController)
app.use(router)
app.mount('#app')

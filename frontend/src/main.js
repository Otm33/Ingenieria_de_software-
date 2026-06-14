import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './styles.css'

import UserService from './services/UserService.js'
import ComercioService from './services/ComercioService.js'
import AuthController from './controllers/AuthController.js'
import AdminController from './controllers/AdminController.js'
import CarteleraController from './controllers/CarteleraController.js'
import TruequeController from './controllers/TruequeController.js'
import ResenaController from './controllers/ResenaController.js'
import ComunidadController from './controllers/ComunidadController.js'
import ComercioController from './controllers/ComercioController.js'

const userService = new UserService('/api/')
const comercioService = new ComercioService('/api/')

const authController = new AuthController(userService)
const adminController = new AdminController(userService)
const carteleraController = new CarteleraController(userService)
const truequeController = new TruequeController(userService)
const resenaController = new ResenaController(userService)
const comunidadController = new ComunidadController(userService)
const comercioController = new ComercioController(comercioService)

const app = createApp(App)

app.provide('authController', authController)
app.provide('adminController', adminController)
app.provide('carteleraController', carteleraController)
app.provide('truequeController', truequeController)
app.provide('resenaController', resenaController)
app.provide('comunidadController', comunidadController)
app.provide('comercioController', comercioController)

app.use(router)
app.mount('#app')

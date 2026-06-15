import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './styles.css'

import AuthController from './controllers/AuthController.js'
import CarteleraController from './controllers/CarteleraController.js'
import ComunidadController from './controllers/ComunidadController.js'
import PerfilController from './controllers/PerfilController.js'
import TruequeController from './controllers/TruequeController.js'
import AdminController from './controllers/AdminController.js'
import ResenaController from './controllers/ResenaController.js'

const authController = new AuthController()
const carteleraController = new CarteleraController()
const comunidadController = new ComunidadController()
const perfilController = new PerfilController()
const truequeController = new TruequeController()
const adminController = new AdminController()
const resenaController = new ResenaController()

const app = createApp(App)

app.provide('authController', authController)
app.provide('carteleraController', carteleraController)
app.provide('comunidadController', comunidadController)
app.provide('perfilController', perfilController)
app.provide('truequeController', truequeController)
app.provide('adminController', adminController)
app.provide('resenaController', resenaController)

app.use(router)
app.mount('#app')

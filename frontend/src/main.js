import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // <-- Asegúrate de que esta línea exista
import axios from 'axios'

axios.defaults.baseURL = 'http://127.0.0.1:8000'

const app = createApp(App)

app.use(router) // <-- ESTA LÍNEA ES CRUCIAL. Si no está, las URLs no cambian nada.
app.mount('#app')

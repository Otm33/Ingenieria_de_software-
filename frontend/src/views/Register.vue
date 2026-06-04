<template>
  <section class="page">
    <div class="page-header">
      <div>
        <p class="eyebrow">Nuevo integrante</p>
        <h2 class="page-title">{{ esComercio ? 'Registro de comercio' : 'Registro de usuario' }}</h2>
        <p class="page-description">
          Crea una cuenta para participar en la comunidad. El correo debe estar autorizado previamente en la columna correcta del CSV.
        </p>
      </div>
    </div>

    <section class="panel">
      <div class="panel__header">
        <h3 class="panel__title">{{ esComercio ? 'Datos del comercio' : 'Datos del usuario' }}</h3>
      </div>

      <form class="panel__body" @submit.prevent="ejecutarRegistro">
        <div class="form-grid">
          <div class="form-group">
            <label for="nombre_real">{{ esComercio ? 'Nombre del comercio' : 'Nombre completo' }}</label>
            <input
              id="nombre_real"
              v-model="form.nombre_real"
              class="input"
              type="text"
              required
              :placeholder="esComercio ? 'Ej. Panaderia Central' : 'Ej. Juan Perez'"
            />
          </div>

          <div class="form-group">
            <label for="email">Correo electronico</label>
            <input
              id="email"
              v-model="form.email"
              class="input"
              type="email"
              required
              placeholder="Ej. juan@correo.com"
            />
          </div>

          <div class="form-group">
            <label for="username">Nombre de usuario</label>
            <input
              id="username"
              v-model="form.username"
              class="input"
              type="text"
              required
              placeholder="Ej. juanperez"
            />
          </div>

          <div class="form-group">
            <label for="password">Contrasena</label>
            <input
              id="password"
              v-model="form.password"
              class="input"
              type="password"
              required
              placeholder="Minimo 8 caracteres"
            />
          </div>
        </div>

        <div class="form-actions">
          <button class="button button--primary" type="submit" :disabled="enviando">
            {{ enviando ? 'Registrando...' : (esComercio ? 'Guardar comercio' : 'Guardar usuario') }}
          </button>
          <button class="button button--secondary" type="button" @click="limpiarFormulario">
            Limpiar
          </button>
        </div>

        <p v-if="feedback" :class="['alert', registroExitoso ? 'alert--success' : 'alert--error']">
          {{ feedback }}
        </p>
      </form>
    </section>
  </section>
</template>

<script setup>
import { inject, ref } from 'vue';

// CAMBIO VISTA: el registro puede vivir debajo del login o como panel administrativo.
const props = defineProps({
  esComercio: {
    type: Boolean,
    default: false,
  },
});
const emit = defineEmits(['registered']);
// CAMBIO VISTA: la vista recibe el controlador instanciado en main.js.
const userController = inject('userController');
const form = ref({ nombre_real: '', email: '', username: '', password: '', es_comercio: props.esComercio });
const feedback = ref('');
const enviando = ref(false);
const registroExitoso = ref(false);

const limpiarFormulario = () => {
  form.value = { nombre_real: '', email: '', username: '', password: '', es_comercio: props.esComercio };
  feedback.value = '';
  registroExitoso.value = false;
};

const ejecutarRegistro = async () => {
  enviando.value = true;
  feedback.value = '';
  registroExitoso.value = false;

  try {
    // CAMBIO VISTA: el registro pasa por controlador -> servicio -> API Django -> BD.
    form.value.es_comercio = props.esComercio;
    await userController.registrarUsuario(form.value);
    const credenciales = { username: form.value.username, password: form.value.password };
    registroExitoso.value = true;
    feedback.value = props.esComercio ? 'Comercio registrado correctamente.' : 'Usuario registrado correctamente.';
    emit('registered', credenciales);
  } catch (err) {
    feedback.value = err.message || 'No se pudo registrar el usuario.';
  } finally {
    enviando.value = false;
  }
};
</script>

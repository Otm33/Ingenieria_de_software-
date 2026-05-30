<template>
  <section class="page">
    <div class="page-header">
      <div>
        <p class="eyebrow">Nuevo integrante</p>
        <h2 class="page-title">Registro de usuario</h2>
        <p class="page-description">
          Crea una cuenta para participar en la comunidad. El correo debe estar autorizado previamente en la lista CSV.
        </p>
      </div>
    </div>

    <section class="panel">
      <div class="panel__header">
        <h3 class="panel__title">Datos del usuario</h3>
      </div>

      <form class="panel__body" @submit.prevent="ejecutarRegistro">
        <div class="form-grid">
          <div class="form-group">
            <label for="nombre_real">Nombre completo</label>
            <input
              id="nombre_real"
              v-model="form.nombre_real"
              class="input"
              type="text"
              required
              placeholder="Ej. Juan Perez"
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
            {{ enviando ? 'Registrando...' : 'Guardar usuario' }}
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
const emit = defineEmits(['registered']);
// CAMBIO VISTA: la vista recibe el controlador instanciado en main.js.
const userController = inject('userController');
const form = ref({ nombre_real: '', email: '', username: '', password: '' });
const feedback = ref('');
const enviando = ref(false);
const registroExitoso = ref(false);

const limpiarFormulario = () => {
  form.value = { nombre_real: '', email: '', username: '', password: '' };
  feedback.value = '';
  registroExitoso.value = false;
};

const ejecutarRegistro = async () => {
  enviando.value = true;
  feedback.value = '';
  registroExitoso.value = false;

  try {
    // CAMBIO VISTA: el registro pasa por controlador -> servicio -> API Django -> BD.
    await userController.registrarUsuario(form.value);
    const credenciales = { username: form.value.username, password: form.value.password };
    registroExitoso.value = true;
    feedback.value = 'Usuario registrado correctamente.';
    emit('registered', credenciales);
  } catch (err) {
    feedback.value = err.message || 'No se pudo registrar el usuario.';
  } finally {
    enviando.value = false;
  }
};
</script>

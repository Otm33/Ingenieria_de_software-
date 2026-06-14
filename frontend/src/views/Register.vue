<template>
  <section class="page register-page">
    <div class="page-header">
      <div>
        <p class="eyebrow">{{ esComercio ? 'Nuevo comercio afiliado' : 'Nuevo integrante' }}</p>
        <h2 class="page-title">{{ esComercio ? 'Registro de comercio' : 'Registro de usuario' }}</h2>
        <p class="page-description">
          {{ esComercio
            ? 'Completa los 3 pasos para afiliar tu comercio. El correo debe estar autorizado en la columna Comercios del CSV y te habilitara la Red Comercial.'
            : 'Completa los 3 pasos para unirte a la comunidad. El correo debe estar autorizado en la columna Usuarios del CSV y publicaras tu primer talento.'
          }}
        </p>
      </div>
    </div>

    <nav class="wizard-progress" aria-label="Progreso del registro">
      <div
        v-for="(etiqueta, indice) in pasos"
        :key="etiqueta"
        :class="['wizard-progress__step', {
          'wizard-progress__step--active': pasoActual === indice + 1,
          'wizard-progress__step--done': pasoActual > indice + 1,
        }]"
      >
        <span class="wizard-progress__number">{{ indice + 1 }}</span>
        <span class="wizard-progress__label">{{ etiqueta }}</span>
      </div>
    </nav>

    <section class="panel">
      <div class="panel__header">
        <h3 class="panel__title">{{ tituloPaso }}</h3>
      </div>

      <form class="panel__body" @submit.prevent="avanzarPaso">
        <!-- Paso 1: Validar correo -->
        <div v-if="pasoActual === 1" class="form-grid">
          <div class="form-group form-group--full">
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
        </div>

        <!-- Paso 2: Credenciales -->
        <div v-else-if="pasoActual === 2" class="form-grid">
          <div class="form-group form-group--full">
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
              minlength="8"
              placeholder="Minimo 8 caracteres"
            />
          </div>

          <div class="form-group">
            <label for="password_confirm">Confirmar contrasena</label>
            <input
              id="password_confirm"
              v-model="form.password_confirm"
              class="input"
              type="password"
              required
              minlength="8"
              placeholder="Repite la contrasena"
            />
          </div>
        </div>

        <!-- Paso 3: Perfil vecino (talento) -->
        <template v-else-if="!esComercio">
          <div class="form-grid">
            <div class="form-group form-group--full">
              <label for="nombre_real">Nombre real</label>
              <input
                id="nombre_real"
                v-model="form.nombre_real"
                class="input"
                type="text"
                required
                placeholder="Ej. Juan Perez"
              />
            </div>

            <div class="form-group form-group--full">
              <label for="categoria">Categoria del primer talento</label>
              <select id="categoria" v-model="form.categoria" class="select" required>
                <option value="">Selecciona una categoria</option>
                <option v-for="categoria in CATEGORIAS" :key="categoria" :value="categoria">
                  {{ categoria }}
                </option>
              </select>
            </div>

            <div class="form-group form-group--full">
              <label for="titulo">Titulo del talento</label>
              <select id="titulo" v-model="form.titulo" class="select" required :disabled="!form.categoria">
                <option value="">Selecciona un titulo</option>
                <option v-for="titulo in titulosDisponibles" :key="titulo" :value="titulo">
                  {{ titulo }}
                </option>
              </select>
            </div>
          </div>

          <div class="form-group form-group--full">
            <label for="descripcion">Descripcion del talento</label>
            <textarea
              id="descripcion"
              v-model="form.descripcion"
              class="textarea"
              rows="4"
              required
              placeholder="Describe que ofreces"
            ></textarea>
          </div>
        </template>

        <!-- Paso 3: Perfil comercial -->
        <template v-else>
          <div class="form-grid">
            <div class="form-group form-group--full">
              <label for="nombre_comercio">Nombre del comercio</label>
              <input
                id="nombre_comercio"
                v-model="form.nombre_real"
                class="input"
                type="text"
                required
                minlength="2"
                placeholder="Ej. Panaderia Central"
              />
            </div>
          </div>

          <p class="register-info">
            Al completar el registro podrás emitir vuelto comercial y aparecerás en el catálogo de la red.
          </p>
        </template>

        <div class="form-actions">
          <button
            v-if="pasoActual > 1"
            class="button button--secondary"
            type="button"
            :disabled="enviando"
            @click="retrocederPaso"
          >
            Atras
          </button>

          <button class="button button--primary" type="submit" :disabled="enviando">
            {{ textoBotonPrincipal }}
          </button>

          <button
            v-if="pasoActual === 1"
            class="button button--secondary"
            type="button"
            :disabled="enviando"
            @click="limpiarFormulario"
          >
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
import { computed, inject, ref, watch } from 'vue';
import { CATEGORIAS, titulosParaCategoria } from '../data/catalogoServicios.js';

const props = defineProps({
  esComercio: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['registered']);

const authController = inject('authController');
const carteleraController = inject('carteleraController');
const pasos = computed(() => (
  props.esComercio
    ? ['Correo', 'Credenciales', 'Perfil comercial']
    : ['Correo', 'Credenciales', 'Perfil y talento']
));
const pasoActual = ref(1);
const form = ref({
  email: '',
  username: '',
  password: '',
  password_confirm: '',
  nombre_real: '',
  categoria: '',
  titulo: '',
  descripcion: '',
});
const feedback = ref('');
const enviando = ref(false);
const registroExitoso = ref(false);

const titulosDisponibles = computed(() => titulosParaCategoria(form.value.categoria));

const tituloPaso = computed(() => {
  if (pasoActual.value === 1) return 'Paso 1 — Validar correo';
  if (pasoActual.value === 2) return 'Paso 2 — Credenciales';
  return props.esComercio ? 'Paso 3 — Perfil comercial' : 'Paso 3 — Perfil inicial y primer talento';
});

const textoBotonPrincipal = computed(() => {
  if (enviando.value) {
    return pasoActual.value === 3 ? 'Guardando...' : 'Validando...';
  }
  if (pasoActual.value === 3) return 'Guardar';
  return 'Continuar';
});

watch(() => form.value.categoria, () => {
  form.value.titulo = '';
});

const limpiarFormulario = () => {
  pasoActual.value = 1;
  form.value = {
    email: '',
    username: '',
    password: '',
    password_confirm: '',
    nombre_real: '',
    categoria: '',
    titulo: '',
    descripcion: '',
  };
  feedback.value = '';
  registroExitoso.value = false;
};

const retrocederPaso = () => {
  feedback.value = '';
  if (pasoActual.value > 1) {
    pasoActual.value -= 1;
  }
};

const validarEmailPaso1 = async () => {
  enviando.value = true;
  feedback.value = '';
  registroExitoso.value = false;

  try {
    await authController.validarEmail(form.value.email, props.esComercio);
    pasoActual.value = 2;
  } catch (err) {
    feedback.value = err.message || 'El correo no esta autorizado para esta comunidad.';
  } finally {
    enviando.value = false;
  }
};

const ejecutarRegistroCompleto = async () => {
  enviando.value = true;
  feedback.value = '';
  registroExitoso.value = false;

  try {
    await authController.completarRegistroNuevoMiembro(form.value, props.esComercio, carteleraController);

    registroExitoso.value = true;
    feedback.value = props.esComercio
      ? 'Comercio registrado correctamente. Ya puedes emitir vuelto en la Red Comercial.'
      : '¡Bienvenido, Miembro Activo! Registro completado.';

    emit('registered', {
      username: form.value.username,
      password: form.value.password,
      esNuevoMiembro: true,
      esComercio: props.esComercio,
    });
  } catch (err) {
    feedback.value = err.message || 'No se pudo completar el registro.';
  } finally {
    enviando.value = false;
  }
};

const avanzarPaso = async () => {
  feedback.value = '';

  if (pasoActual.value === 1) {
    await validarEmailPaso1();
    return;
  }

  if (pasoActual.value === 2) {
    enviando.value = true;
    try {
      await authController.validarPasoCredenciales(form.value);
      pasoActual.value = 3;
    } catch (err) {
      feedback.value = err.message || 'Revisa las credenciales ingresadas.';
    } finally {
      enviando.value = false;
    }
    return;
  }

  await ejecutarRegistroCompleto();
};
</script>

<style scoped>
.register-info {
  margin: 0;
  padding: 12px 14px;
  border-radius: 8px;
  color: var(--primary-dark);
  background: #e8f2f8;
  font-size: 0.95rem;
  line-height: 1.45;
}
</style>

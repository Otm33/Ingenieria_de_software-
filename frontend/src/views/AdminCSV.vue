<template>
  <section class="page">
    <div class="page-header">
      <div>
        <p class="eyebrow">Administracion</p>
        <h2 class="page-title">Carga de usuarios autorizados</h2>
        <p class="page-description">
          Sube un archivo CSV con los correos permitidos para que puedan registrarse en TuTrueque.
        </p>
      </div>
    </div>

    <section class="panel">
      <div class="panel__header">
        <h3 class="panel__title">Archivo CSV</h3>
      </div>

      <div class="panel__body">
        <div class="file-box">
          <div class="form-group">
            <label for="archivo_csv">Seleccionar archivo</label>
            <input id="archivo_csv" class="input" type="file" accept=".csv" @change="seleccionarArchivo" />
          </div>

          <div class="form-actions">
            <button class="button button--accent" type="button" :disabled="procesando" @click="subirArchivo">
              {{ procesando ? 'Procesando...' : 'Procesar lista' }}
            </button>
          </div>
        </div>

        <p v-if="mensaje" class="alert alert--success">{{ mensaje }}</p>
        <p v-if="error" class="alert alert--error">{{ error }}</p>
      </div>
    </section>

    <section class="panel">
      <div class="panel__header">
        <h3 class="panel__title">Formato esperado</h3>
      </div>
      <div class="panel__body">
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Columna</th>
                <th>Descripcion</th>
                <th>Ejemplo</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>email</td>
                <td>Correo autorizado para registro</td>
                <td>persona@correo.com</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  </section>
</template>

<script setup>
import { inject, ref } from 'vue';

// CAMBIO VISTA: la vista delega la persistencia CSV al controlador instanciado.
const userController = inject('userController');
const archivo = ref(null);
const mensaje = ref('');
const error = ref('');
const procesando = ref(false);

const seleccionarArchivo = (event) => {
  const file = event.target.files[0];

  mensaje.value = '';
  error.value = '';

  if (!file) {
    archivo.value = null;
    return;
  }

  if (file.name.toLowerCase().endsWith('.csv')) {
    archivo.value = file;
    return;
  }

  archivo.value = null;
  event.target.value = '';
  error.value = 'Formato incorrecto. Solo se acepta .csv.';
};

const subirArchivo = async () => {
  if (!archivo.value) {
    error.value = 'Selecciona un archivo CSV antes de procesar.';
    return;
  }

  mensaje.value = '';
  error.value = '';
  procesando.value = true;

  try {
    // CAMBIO VISTA: el archivo pasa por controlador -> servicio -> API Django -> BD.
    const response = await userController.cargarUsuariosAutorizados(archivo.value);
    mensaje.value = response.mensaje || response.message || 'Archivo procesado correctamente.';
  } catch (err) {
    error.value = err.message || 'Error al procesar el archivo.';
  } finally {
    procesando.value = false;
  }
};
</script>

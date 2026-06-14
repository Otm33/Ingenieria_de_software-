<template>
  <section class="page">
    <div class="page-header">
      <div>
        <p class="eyebrow">Administracion</p>
        <h2 class="page-title">Carga de usuarios autorizados</h2>
        <p class="page-description">
          Sube un archivo CSV con correos separados para usuarios y comercios autorizados.
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
                <td>email Usuarios</td>
                <td>Correo autorizado para registro de usuarios</td>
                <td>persona@correo.com</td>
              </tr>
              <tr>
                <td>email Comercios</td>
                <td>Correo autorizado para registro de comercios</td>
                <td>negocio@correo.com</td>
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
const adminController = inject('adminController');
const archivo = ref(null);
const mensaje = ref('');
const error = ref('');
const procesando = ref(false);

const seleccionarArchivo = (event) => {
  const file = event.target.files[0];

  mensaje.value = '';
  error.value = '';

  try {
    const resultado = adminController.validarSeleccionArchivo(file);
    archivo.value = resultado.archivo;
  } catch (err) {
    archivo.value = null;
    event.target.value = '';
    error.value = err.message || 'Formato incorrecto. Solo se acepta .csv.';
  }
};

const subirArchivo = async () => {
  mensaje.value = '';
  error.value = '';
  procesando.value = true;

  try {
    const response = await adminController.cargarUsuariosAutorizados(archivo.value);
    mensaje.value = response.mensaje || response.message || 'Archivo procesado correctamente.';
  } catch (err) {
    error.value = err.message || 'Error al procesar el archivo.';
  } finally {
    procesando.value = false;
  }
};
</script>

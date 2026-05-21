<template>
  <div class="max-w-md mx-auto bg-white p-8 rounded-xl shadow-md mt-12">
    <h2 class="text-2xl font-bold mb-6 text-gray-800">Registro en TuTrueque</h2>
    <form @submit.prevent="ejecutarRegistro" class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700">Nombre Real</label>
        <input v-model="form.nombre_real" type="text" required class="w-full border p-2 rounded mt-1" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Correo Electrónico</label>
        <input v-model="form.email" type="email" required class="w-full border p-2 rounded mt-1" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Username Único</label>
        <input v-model="form.username" type="text" required class="w-full border p-2 rounded mt-1" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Contraseña</label>
        <input v-model="form.password" type="password" required class="w-full border p-2 rounded mt-1" />
      </div>
      <button type="submit" class="w-full bg-green-600 text-white p-2 rounded font-bold hover:bg-green-700">Registrar Cuenta</button>
    </form>
    <p v-if="feedback" class="mt-4 text-center font-medium text-red-600">{{ feedback }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';

const router = useRouter();
const form = ref({ nombre_real: '', email: '', username: '', password: '' });
const feedback = ref('');

const ejecutarRegistro = async () => {
  try {
    await axios.post('/api/registro/', form.value);
    router.push('/');
  } catch (err) {
    feedback.value = err.response?.data?.error || "Usuario no autorizado para esta comunidad.";
  }
};
</script>

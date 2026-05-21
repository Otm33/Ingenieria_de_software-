<template>
  <div id="app">
    <nav style="background: #2563eb; padding: 15px; color: white; display: flex; gap: 15px;">
      <strong style="margin-right: 20px;">🔄 TuTrueque</strong>
      <router-link to="/" style="color: white; text-decoration: none;">Cartelera</router-link> |
      <router-link to="/register" style="color: white; text-decoration: none;">Registrarse</router-link> |
      <router-link to="/admin-csv" style="color: white; text-decoration: none;">Panel CSV</router-link>
    </nav>

    <div style="padding: 20px;">
      <router-view></router-view>
    </div>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

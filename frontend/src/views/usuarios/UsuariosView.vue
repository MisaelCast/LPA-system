<script setup lang="ts">
import { onMounted } from 'vue'
import { useUsuariosStore } from '@/stores/usuarios'

const store = useUsuariosStore()

onMounted(() => {
  store.cargarUsuarios()
})

function estadoLabel(activo: boolean): string {
  return activo ? 'Activo' : 'Inactivo'
}
</script>

<template>
  <h1>Usuarios</h1>

  <p v-if="store.cargando">Cargando…</p>

  <template v-else>
    <table v-if="store.usuarios.length">
      <thead>
        <tr>
          <th>Nombre</th>
          <th>Correo</th>
          <th>Rol</th>
          <th>Estado</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in store.usuarios" :key="u.id">
          <td>{{ u.nombre }}</td>
          <td>{{ u.correo }}</td>
          <td>{{ u.rol_id }}</td>
          <td>{{ estadoLabel(u.activo) }}</td>
        </tr>
      </tbody>
    </table>

    <p v-else>No hay usuarios registrados.</p>
  </template>
</template>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 0.5rem;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

th {
  text-align: left;
  padding: 0.75rem 1rem;
  background: #f8fafc;
  color: #475569;
  font-size: 0.8rem;
  font-weight: 600;
  border-bottom: 1px solid #e2e8f0;
}

td {
  padding: 0.625rem 1rem;
  border-bottom: 1px solid #f1f5f9;
  font-size: 0.875rem;
  color: #334155;
}

tr:last-child td {
  border-bottom: none;
}
</style>

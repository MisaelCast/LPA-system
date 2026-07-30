<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useUsuariosStore } from '@/stores/usuarios'
import type { Usuario } from '@/types/auth'

const store = useUsuariosStore()

const editando = ref<Usuario | null>(null)
const formNombre = ref('')
const formCorreo = ref('')
const formRolId = ref(0)
const mensaje = ref('')
const error = ref('')
const guardando = ref(false)

onMounted(() => {
  store.cargarUsuarios()
})

function iniciarEdicion(u: Usuario) {
  editando.value = u
  formNombre.value = u.nombre
  formCorreo.value = u.correo
  formRolId.value = u.rol_id
  mensaje.value = ''
  error.value = ''
}

function cancelarEdicion() {
  editando.value = null
}

async function guardarCambios() {
  if (!editando.value) return
  error.value = ''
  guardando.value = true

  try {
    await store.actualizar(editando.value.id, {
      nombre: formNombre.value,
      correo: formCorreo.value,
      rol_id: formRolId.value,
    })
    mensaje.value = 'Usuario actualizado correctamente.'
    editando.value = null
  } catch {
    error.value = 'Error al actualizar el usuario.'
  } finally {
    guardando.value = false
  }
}

function estadoLabel(activo: boolean): string {
  return activo ? 'Activo' : 'Inactivo'
}
</script>

<template>
  <h1>Usuarios</h1>

  <p v-if="mensaje" class="exito">{{ mensaje }}</p>
  <p v-if="error" class="fallo">{{ error }}</p>

  <div v-if="store.cargando">Cargando…</div>

  <template v-else>
    <table v-if="store.usuarios.length">
      <thead>
        <tr>
          <th>Nombre</th>
          <th>Correo</th>
          <th>Rol</th>
          <th>Estado</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in store.usuarios" :key="u.id">
          <td>{{ u.nombre }}</td>
          <td>{{ u.correo }}</td>
          <td>{{ u.rol_id }}</td>
          <td>{{ estadoLabel(u.activo) }}</td>
          <td>
            <button class="btn-editar" @click="iniciarEdicion(u)">Editar</button>
          </td>
        </tr>
      </tbody>
    </table>

    <p v-else>No hay usuarios registrados.</p>

    <div v-if="editando" class="form-edicion">
      <h2>Editar usuario</h2>

      <div class="field">
        <label for="edit-nombre">Nombre</label>
        <input id="edit-nombre" v-model="formNombre" required />
      </div>

      <div class="field">
        <label for="edit-correo">Correo</label>
        <input id="edit-correo" v-model="formCorreo" type="email" required />
      </div>

      <div class="field">
        <label for="edit-rol">Rol</label>
        <input id="edit-rol" v-model.number="formRolId" type="number" required />
      </div>

      <div class="acciones">
        <button class="btn-guardar" :disabled="guardando" @click="guardarCambios">
          {{ guardando ? 'Guardando…' : 'Actualizar usuario' }}
        </button>
        <button class="btn-cancelar" @click="cancelarEdicion">Cancelar</button>
      </div>
    </div>
  </template>
</template>

<style scoped>
.exito {
  background: #f0fdf4;
  color: #16a34a;
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.fallo {
  background: #fef2f2;
  color: #dc2626;
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 0.5rem;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  margin-top: 1rem;
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

.btn-editar {
  background: #e2e8f0;
  border: none;
  padding: 0.25rem 0.75rem;
  border-radius: 0.25rem;
  font-size: 0.8rem;
  cursor: pointer;
  color: #334155;
}

.btn-editar:hover {
  background: #cbd5e1;
}

.form-edicion {
  margin-top: 1.5rem;
  background: #fff;
  padding: 1.5rem;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  max-width: 480px;
}

.form-edicion h2 {
  margin: 0 0 1rem;
  font-size: 1.125rem;
  color: #1e293b;
}

.field {
  margin-bottom: 0.75rem;
}

.field label {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 0.8rem;
  color: #475569;
}

.field input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  box-sizing: border-box;
}

.field input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 1px #3b82f6;
}

.acciones {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.btn-guardar {
  background: #1e293b;
  color: #fff;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  cursor: pointer;
}

.btn-guardar:hover {
  background: #334155;
}

.btn-guardar:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-cancelar {
  background: #e2e8f0;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  cursor: pointer;
  color: #334155;
}

.btn-cancelar:hover {
  background: #cbd5e1;
}
</style>

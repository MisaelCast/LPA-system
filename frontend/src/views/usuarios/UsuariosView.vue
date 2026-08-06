<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useUsuariosStore } from '@/stores/usuarios'
import { useAuthStore } from '@/stores/auth'
import { obtenerRoles } from '@/services/rol.service'
import type { Usuario } from '@/types/auth'
import type { Rol } from '@/types/rol'

const store = useUsuariosStore()
const authStore = useAuthStore()

const roles = ref<Rol[]>([])

/* --- Creación --- */
const crearNombre = ref('')
const crearCorreo = ref('')
const crearContrasena = ref('')
const crearRolId = ref(0)
const creando = ref(false)

/* --- Edición --- */
const editando = ref<Usuario | null>(null)
const editNombre = ref('')
const editCorreo = ref('')
const editRolId = ref(0)
const guardando = ref(false)

/* --- Mensajes --- */
const mensaje = ref('')
const error = ref('')

onMounted(async () => {
  store.cargarUsuarios()
  roles.value = await obtenerRoles()
})

/* ——— Crear ——— */
async function handleCrear() {
  mensaje.value = ''
  error.value = ''
  creando.value = true

  try {
    await store.crear({
      nombre: crearNombre.value,
      correo: crearCorreo.value,
      contrasena: crearContrasena.value,
      rol_id: crearRolId.value,
      activo: true,
    })
    mensaje.value = 'Usuario creado correctamente.'
    crearNombre.value = ''
    crearCorreo.value = ''
    crearContrasena.value = ''
    crearRolId.value = 0
  } catch (err: unknown) {
    if (err && typeof err === 'object' && 'response' in err) {
      const axiosErr = err as { response: { status: number; data?: { detail?: string } } }
      if (axiosErr.response.status === 403) {
        error.value = 'No tiene permisos para realizar esta acción.'
      } else {
        error.value = axiosErr.response.data?.detail || 'Error al crear el usuario.'
      }
    } else {
      error.value = 'Error al crear el usuario.'
    }
  } finally {
    creando.value = false
  }
}

/* ——— Editar ——— */
function iniciarEdicion(u: Usuario) {
  editando.value = u
  editNombre.value = u.nombre
  editCorreo.value = u.correo
  editRolId.value = u.rol_id
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
      nombre: editNombre.value,
      correo: editCorreo.value,
      rol_id: editRolId.value,
    })
    mensaje.value = 'Usuario actualizado correctamente.'
    editando.value = null
  } catch (err: unknown) {
    if (err && typeof err === 'object' && 'response' in err) {
      const axiosErr = err as { response: { status: number } }
      error.value = axiosErr.response.status === 403
        ? 'No tiene permisos para realizar esta acción.'
        : 'Error al actualizar el usuario.'
    } else {
      error.value = 'Error al actualizar el usuario.'
    }
  } finally {
    guardando.value = false
  }
}

/* ——— Estado ——— */
async function toggleEstado(u: Usuario) {
  const accion = u.activo ? 'desactivar' : 'activar'
  if (!window.confirm(`¿Desea ${accion} este usuario?`)) return

  mensaje.value = ''
  error.value = ''

  try {
    await store.cambiarEstado(u.id, !u.activo)
    const estado = u.activo ? 'desactivado' : 'activado'
    mensaje.value = `Usuario ${estado} correctamente.`
  } catch (err: unknown) {
    if (err && typeof err === 'object' && 'response' in err) {
      const axiosErr = err as { response: { status: number } }
      error.value = axiosErr.response.status === 403
        ? 'No tiene permisos para realizar esta acción.'
        : 'Error al cambiar el estado del usuario.'
    } else {
      error.value = 'Error al cambiar el estado del usuario.'
    }
  }
}
</script>

<template>
  <div class="page">
    <h1>Usuarios</h1>

    <!-- Mensajes -->
    <p v-if="mensaje" class="msg exito">{{ mensaje }}</p>
    <p v-if="error" class="msg fallo">{{ error }}</p>

    <!-- Formulario de creación -->
    <form v-if="authStore.isAdmin" class="card" @submit.prevent="handleCrear">
      <h2 class="card-title">Nuevo usuario</h2>

      <div class="form-row">
        <label class="field">
          <span>Nombre</span>
          <input v-model="crearNombre" required />
        </label>

        <label class="field">
          <span>Correo</span>
          <input v-model="crearCorreo" type="email" required />
        </label>

        <label class="field">
          <span>Contraseña</span>
          <input v-model="crearContrasena" type="password" required />
        </label>

        <label class="field field-sm">
          <span>Rol</span>
          <select v-model.number="crearRolId" required>
            <option :value="0" disabled>Seleccione</option>
            <option v-for="r in roles" :key="r.id" :value="r.id">{{ r.nombre }}</option>
          </select>
        </label>

        <div class="field field-btn">
          <button class="btn btn-primary" type="submit" :disabled="creando">
            {{ creando ? 'Creando…' : 'Crear usuario' }}
          </button>
        </div>
      </div>
    </form>

    <!-- Formulario de edición -->
    <form v-if="editando" class="card" @submit.prevent="guardarCambios">
      <h2 class="card-title">Editar usuario</h2>

      <div class="form-row">
        <label class="field">
          <span>Nombre</span>
          <input v-model="editNombre" required />
        </label>

        <label class="field">
          <span>Correo</span>
          <input v-model="editCorreo" type="email" required />
        </label>

        <label class="field field-sm">
          <span>Rol</span>
          <select v-model.number="editRolId" required>
            <option v-for="r in roles" :key="r.id" :value="r.id">{{ r.nombre }}</option>
          </select>
        </label>

        <div class="field field-btn">
          <button class="btn btn-primary" type="submit" :disabled="guardando">
            {{ guardando ? 'Guardando…' : 'Actualizar' }}
          </button>
          <button class="btn btn-secondary" type="button" @click="cancelarEdicion">
            Cancelar
          </button>
        </div>
      </div>
    </form>

    <!-- Tabla -->
    <div v-if="store.cargando" class="card">Cargando…</div>

    <div v-else-if="store.usuarios.length === 0" class="card">
      No hay usuarios registrados.
    </div>

    <table v-else class="table">
      <thead>
        <tr>
          <th>Nombre</th>
          <th>Correo</th>
          <th>Rol</th>
          <th>Estado</th>
          <th v-if="authStore.isAdmin" class="th-acciones">Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in store.usuarios" :key="u.id">
          <td>{{ u.nombre }}</td>
          <td>{{ u.correo }}</td>
          <td>{{ u.rol_nombre }}</td>
          <td>
            <span class="badge" :class="u.activo ? 'badge-activo' : 'badge-inactivo'">
              {{ u.activo ? 'Activo' : 'Inactivo' }}
            </span>
          </td>
          <td v-if="authStore.isAdmin" class="td-acciones">
            <button class="btn btn-sm btn-secondary" @click="iniciarEdicion(u)">Editar</button>
            <button
              class="btn btn-sm"
              :class="u.activo ? 'btn-danger' : 'btn-success'"
              @click="toggleEstado(u)"
            >
              {{ u.activo ? 'Desactivar' : 'Activar' }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
/* ——— Layout ——— */
.page {
  max-width: 1200px;
}

/* ——— Mensajes ——— */
.msg {
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.exito {
  background: #f0fdf4;
  color: #16a34a;
}

.fallo {
  background: #fef2f2;
  color: #dc2626;
}

/* ——— Card ——— */
.card {
  background: #fff;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.25rem;
}

.card-title {
  margin: 0 0 0.75rem;
  font-size: 1rem;
  color: #1e293b;
}

/* ——— Form ——— */
.form-row {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1 1 180px;
}

.field span {
  font-size: 0.8rem;
  color: #475569;
  font-weight: 500;
}

.field input,
.field select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.field input:focus,
.field select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 1px #3b82f6;
}

.field-sm {
  flex: 0 0 100px;
}

.field-btn {
  flex: 0 0 auto;
  flex-direction: row;
  gap: 0.5rem;
}

/* ——— Botones ——— */
.btn {
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #1e293b;
  color: #fff;
  padding: 0.5rem 1rem;
}

.btn-primary:hover {
  background: #334155;
}

.btn-secondary {
  background: #e2e8f0;
  color: #334155;
  padding: 0.5rem 1rem;
}

.btn-secondary:hover {
  background: #cbd5e1;
}

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.8rem;
}

.btn-danger {
  background: #fef2f2;
  color: #dc2626;
}

.btn-danger:hover { background: #fee2e2; }

.btn-success {
  background: #f0fdf4;
  color: #16a34a;
}

.btn-success:hover { background: #dcfce7; }

/* ——— Badge ——— */
.badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-activo {
  background: #dcfce7;
  color: #16a34a;
}

.badge-inactivo {
  background: #fee2e2;
  color: #dc2626;
}

/* ——— Tabla ——— */
.table {
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
  border-bottom: 2px solid #e2e8f0;
}

td {
  padding: 0.625rem 1rem;
  border-bottom: 1px solid #f1f5f9;
  font-size: 0.875rem;
  color: #334155;
}

tr:last-child td { border-bottom: none; }

.th-acciones,
.td-acciones {
  text-align: right;
  white-space: nowrap;
}

.td-acciones {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}
</style>

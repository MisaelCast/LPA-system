<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useCapasStore } from '@/stores/capas'
import { useAuthStore } from '@/stores/auth'
import type { Capa } from '@/types/capa'

const store = useCapasStore()
const authStore = useAuthStore()

const formNombre = ref('')
const formDescripcion = ref('')
const formGuardando = ref(false)

const capaEditandoId = ref<number | null>(null)
const capaEditNombre = ref('')
const capaEditDescripcion = ref('')
const capaEditGuardando = ref(false)

const mensaje = ref('')
const error = ref('')

onMounted(async () => {
  await store.cargarCapas()
})

function mostrarError(prefix: string, err: unknown) {
  if (err && typeof err === 'object' && 'response' in err) {
    const axiosErr = err as { response: { status: number; data?: { detail?: string } } }
    if (axiosErr.response.status === 403) {
      error.value = 'No tiene permisos para realizar esta acción.'
    } else {
      error.value = axiosErr.response.data?.detail || `Error al ${prefix}.`
    }
  } else {
    error.value = `Error al ${prefix}.`
  }
}

async function handleCrear() {
  mensaje.value = ''
  error.value = ''
  formGuardando.value = true

  try {
    await store.crear({
      nombre: formNombre.value,
      descripcion: formDescripcion.value || undefined,
      activa: true,
    })
    mensaje.value = 'Capa creada correctamente.'
    formNombre.value = ''
    formDescripcion.value = ''
  } catch (err: unknown) {
    mostrarError('crear la capa', err)
  } finally {
    formGuardando.value = false
  }
}

function iniciarEdicion(c: Capa) {
  capaEditandoId.value = c.id
  capaEditNombre.value = c.nombre
  capaEditDescripcion.value = c.descripcion || ''
}

function cancelarEdicion() {
  capaEditandoId.value = null
  capaEditNombre.value = ''
  capaEditDescripcion.value = ''
}

async function guardarEdicion() {
  if (!capaEditandoId.value) return
  error.value = ''
  capaEditGuardando.value = true

  try {
    await store.actualizar(capaEditandoId.value, {
      nombre: capaEditNombre.value,
      descripcion: capaEditDescripcion.value || undefined,
    })
    mensaje.value = 'Capa actualizada correctamente.'
    capaEditandoId.value = null
    capaEditNombre.value = ''
    capaEditDescripcion.value = ''
  } catch (err: unknown) {
    mostrarError('actualizar la capa', err)
  } finally {
    capaEditGuardando.value = false
  }
}

async function eliminarCapa(c: Capa) {
  if (!window.confirm(`¿Está seguro de que desea eliminar la capa "${c.nombre}"?\n\nEsta acción no se puede deshacer.`)) return

  mensaje.value = ''
  error.value = ''

  try {
    await store.eliminar(c.id)
    mensaje.value = 'Capa eliminada correctamente.'
  } catch (err: unknown) {
    mostrarError('eliminar la capa', err)
  }
}
</script>

<template>
  <div class="page">
    <h1>Capas</h1>

    <p v-if="mensaje" class="msg msg-ok">{{ mensaje }}</p>
    <p v-if="error" class="msg msg-err">{{ error }}</p>

    <form v-if="authStore.isAdmin" class="bar" @submit.prevent="handleCrear">
      <div class="bar-fields">
        <label class="bar-field bar-field--name">
          <span>Nombre</span>
          <input v-model="formNombre" placeholder="Ej: Auditor" required />
        </label>
        <label class="bar-field bar-field--desc">
          <span>Descripcion</span>
          <input v-model="formDescripcion" placeholder="Opcional" />
        </label>
      </div>
      <button class="btn btn-dark" type="submit" :disabled="formGuardando">
        {{ formGuardando ? 'Guardando…' : 'Crear capa' }}
      </button>
    </form>

    <div v-if="store.cargando" class="msg msg-info">Cargando…</div>

    <div v-else-if="store.capas.length === 0" class="msg msg-info">
      No hay capas registradas.
    </div>

    <table v-else class="table">
      <thead>
        <tr>
          <th class="col-nombre">Nombre</th>
          <th class="col-desc">Descripcion</th>
          <th class="col-estado">Estado</th>
          <th v-if="authStore.isAdmin" class="col-acciones">Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="c in store.capas"
          :key="c.id"
          :class="{ 'row-inactiva': !c.activa }"
        >
          <td class="col-nombre">
            <template v-if="capaEditandoId === c.id">
              <input
                v-model="capaEditNombre"
                class="inline-input"
                @keyup.escape="cancelarEdicion"
                @keyup.enter="guardarEdicion"
              />
            </template>
            <template v-else>
              {{ c.nombre }}
            </template>
          </td>
          <td class="col-desc">
            <template v-if="capaEditandoId === c.id">
              <input
                v-model="capaEditDescripcion"
                class="inline-input"
                @keyup.escape="cancelarEdicion"
                @keyup.enter="guardarEdicion"
              />
            </template>
            <template v-else>
              {{ c.descripcion || '—' }}
            </template>
          </td>
          <td class="col-estado">
            <span class="badge" :class="c.activa ? 'badge-on' : 'badge-off'">
              {{ c.activa ? 'Activa' : 'Inactiva' }}
            </span>
          </td>
          <td v-if="authStore.isAdmin" class="col-acciones">
            <template v-if="capaEditandoId === c.id">
              <button
                class="chip-btn chip-btn--ok"
                :disabled="capaEditGuardando"
                @click="guardarEdicion"
              >
                ✓
              </button>
              <button class="chip-btn chip-btn--cancel" @click="cancelarEdicion">
                ✕
              </button>
            </template>
            <template v-else>
              <button class="btn btn-sm btn-secondary" @click="iniciarEdicion(c)">
                Editar
              </button>
              <button class="btn btn-sm btn-danger" @click="eliminarCapa(c)">
                Eliminar
              </button>
            </template>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.page {
  max-width: 900px;
}

h1 {
  margin: 0 0 1rem;
  font-size: 1.25rem;
  color: #1e293b;
}

.msg {
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.8rem;
  margin-bottom: 0.75rem;
}

.msg-ok {
  background: #f0fdf4;
  color: #16a34a;
}

.msg-err {
  background: #fef2f2;
  color: #dc2626;
}

.msg-info {
  background: #f8fafc;
  color: #64748b;
}

.bar {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
  background: #fff;
  border-radius: 0.375rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
  border: 1px solid #e2e8f0;
}

.bar-fields {
  display: flex;
  gap: 0.75rem;
  flex: 1;
}

.bar-field {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.bar-field span {
  font-size: 0.7rem;
  color: #94a3b8;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.bar-field input {
  padding: 0.4rem 0.6rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.25rem;
  font-size: 0.85rem;
  min-width: 0;
}

.bar-field input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 1px #3b82f6;
}

.bar-field--name {
  flex: 1 1 200px;
}

.bar-field--desc {
  flex: 2 1 300px;
}

.table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 0.375rem;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
}

th {
  text-align: left;
  padding: 0.5rem 0.75rem;
  background: #f8fafc;
  color: #64748b;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  border-bottom: 1px solid #e2e8f0;
}

td {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid #f1f5f9;
  font-size: 0.85rem;
  color: #334155;
  vertical-align: middle;
}

tr:last-child td {
  border-bottom: none;
}

.row-inactiva {
  opacity: 0.5;
}

.col-nombre {
  width: 25%;
}

.col-desc {
  width: 45%;
}

.col-estado {
  width: 15%;
}

.col-acciones {
  width: 15%;
  text-align: right;
}

.col-acciones {
  display: flex;
  gap: 0.35rem;
  justify-content: flex-end;
}

.inline-input {
  width: calc(100% - 1rem);
  padding: 0.35rem 0.5rem;
  border: 1px solid #93c5fd;
  border-radius: 0.25rem;
  font-size: 0.85rem;
  background: #eff6ff;
}

.inline-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.badge {
  display: inline-block;
  padding: 0.125rem 0.45rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
}

.badge-on {
  background: #dcfce7;
  color: #16a34a;
}

.badge-off {
  background: #fee2e2;
  color: #dc2626;
}

.btn {
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.8rem;
  vertical-align: middle;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-dark {
  background: #1e293b;
  color: #fff;
  padding: 0.45rem 0.9rem;
  font-size: 0.85rem;
  white-space: nowrap;
  border-radius: 0.25rem;
  flex-shrink: 0;
}

.btn-dark:hover {
  background: #334155;
}

.btn-secondary {
  background: #e2e8f0;
  color: #334155;
  padding: 0.3rem 0.6rem;
}

.btn-secondary:hover {
  background: #cbd5e1;
}

.btn-sm {
  padding: 0.25rem 0.6rem;
  font-size: 0.75rem;
}

.btn-danger {
  background: #fef2f2;
  color: #dc2626;
}

.btn-danger:hover {
  background: #fee2e2;
}

.btn-success {
  background: #f0fdf4;
  color: #16a34a;
}

.btn-success:hover {
  background: #dcfce7;
}

.chip-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.1rem;
  height: 1.1rem;
  border: none;
  background: transparent;
  border-radius: 0.15rem;
  cursor: pointer;
  font-size: 0.65rem;
  line-height: 1;
  padding: 0;
  color: #94a3b8;
  transition: color 0.15s, background 0.15s;
}

.chip-btn:hover {
  color: #475569;
  background: #e2e8f0;
}

.chip-btn--ok {
  color: #16a34a;
}

.chip-btn--ok:hover {
  color: #16a34a;
  background: #dcfce7;
}

.chip-btn--cancel {
  color: #dc2626;
}

.chip-btn--cancel:hover {
  color: #dc2626;
  background: #fee2e2;
}
</style>

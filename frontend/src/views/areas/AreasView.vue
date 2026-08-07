<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAreasStore } from '@/stores/areas'
import { useAuthStore } from '@/stores/auth'
import type { Area, Celula } from '@/types/area'

const store = useAreasStore()
const authStore = useAuthStore()

/* --- Área: creación --- */
const crearNombre = ref('')
const creando = ref(false)

/* --- Área: edición --- */
const editando = ref<Area | null>(null)
const editNombre = ref('')
const guardando = ref(false)

/* --- Área expandida para ver/mostrar células --- */
const areaExpandida = ref<number | null>(null)

/* --- Célula: creación --- */
const nuevaCelulaNumero = ref<number | null>(null)
const creandoCelula = ref(false)

/* --- Célula: edición --- */
const celulaEditando = ref<Celula | null>(null)
const celulaEditNumero = ref<number | null>(null)
const guardandoCelula = ref(false)

/* --- Mensajes --- */
const mensaje = ref('')
const error = ref('')

onMounted(() => {
  store.cargarAreas()
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

/* ——— Área: CRUD ——— */
async function handleCrear() {
  mensaje.value = ''
  error.value = ''
  creando.value = true

  try {
    await store.crear({ nombre: crearNombre.value, activa: true })
    mensaje.value = 'Área creada correctamente.'
    crearNombre.value = ''
  } catch (err: unknown) {
    mostrarError('crear el área', err)
  } finally {
    creando.value = false
  }
}

function iniciarEdicion(a: Area) {
  editando.value = a
  editNombre.value = a.nombre
  mensaje.value = ''
  error.value = ''
  // Al editar, expandir las células automáticamente
  toggleCélulas(a.id)
}

function cancelarEdicion() {
  editando.value = null
}

async function guardarCambios() {
  if (!editando.value) return
  error.value = ''
  guardando.value = true

  try {
    await store.actualizar(editando.value.id, { nombre: editNombre.value })
    mensaje.value = 'Área actualizada correctamente.'
    editando.value = null
  } catch (err: unknown) {
    mostrarError('actualizar el área', err)
  } finally {
    guardando.value = false
  }
}

async function toggleEstadoArea(a: Area) {
  const accion = a.activa ? 'desactivar' : 'activar'
  if (!window.confirm(`¿Desea ${accion} esta área?`)) return

  mensaje.value = ''
  error.value = ''

  try {
    await store.cambiarEstado(a.id, !a.activa)
    const estado = a.activa ? 'desactivada' : 'activada'
    mensaje.value = `Área ${estado} correctamente.`
  } catch (err: unknown) {
    mostrarError('cambiar el estado del área', err)
  }
}

/* ——— Células: expandir/colapsar ——— */
function toggleCélulas(areaId: number) {
  if (areaExpandida.value === areaId) {
    areaExpandida.value = null
    return
  }
  areaExpandida.value = areaId
  store.cargarCelulas(areaId)
}

/* ——— Célula: CRUD ——— */
async function agregarCelula() {
  if (!areaExpandida.value || !nuevaCelulaNumero.value) return
  error.value = ''
  creandoCelula.value = true

  try {
    await store.crearCelulaEnArea(areaExpandida.value, {
      numero: nuevaCelulaNumero.value,
      activa: true,
    })
    mensaje.value = 'Célula agregada correctamente.'
    nuevaCelulaNumero.value = null
  } catch (err: unknown) {
    mostrarError('agregar la célula', err)
  } finally {
    creandoCelula.value = false
  }
}

function iniciarEdicionCelula(c: Celula) {
  celulaEditando.value = c
  celulaEditNumero.value = c.numero
  mensaje.value = ''
  error.value = ''
}

function cancelarEdicionCelula() {
  celulaEditando.value = null
  celulaEditNumero.value = null
}

async function guardarCambiosCelula() {
  if (!celulaEditando.value || !areaExpandida.value || !celulaEditNumero.value) return
  error.value = ''
  guardandoCelula.value = true

  try {
    await store.actualizarCelulaEnArea(
      celulaEditando.value.id,
      areaExpandida.value,
      { numero: celulaEditNumero.value },
    )
    mensaje.value = 'Célula actualizada correctamente.'
    celulaEditando.value = null
    celulaEditNumero.value = null
  } catch (err: unknown) {
    mostrarError('actualizar la célula', err)
  } finally {
    guardandoCelula.value = false
  }
}

async function toggleEstadoCelula(c: Celula) {
  if (!areaExpandida.value) return
  const accion = c.activa ? 'desactivar' : 'activar'
  if (!window.confirm(`¿Desea ${accion} esta célula?`)) return

  mensaje.value = ''
  error.value = ''

  try {
    await store.cambiarEstadoCelulaEnArea(c.id, areaExpandida.value, !c.activa)
    const estado = c.activa ? 'desactivada' : 'activada'
    mensaje.value = `Célula ${estado} correctamente.`
  } catch (err: unknown) {
    mostrarError('cambiar el estado de la célula', err)
  }
}
</script>

<template>
  <div class="page">
    <h1>Áreas</h1>

    <!-- Mensajes -->
    <p v-if="mensaje" class="msg exito">{{ mensaje }}</p>
    <p v-if="error" class="msg fallo">{{ error }}</p>

    <!-- Formulario de creación de área -->
    <form v-if="authStore.isAdmin" class="card" @submit.prevent="handleCrear">
      <h2 class="card-title">Nueva área</h2>

      <div class="form-row">
        <label class="field">
          <span>Nombre</span>
          <input v-model="crearNombre" required />
        </label>

        <div class="field field-btn">
          <button class="btn btn-primary" type="submit" :disabled="creando">
            {{ creando ? 'Creando…' : 'Crear área' }}
          </button>
        </div>
      </div>
    </form>

    <!-- Formulario de edición de área -->
    <form v-if="editando" class="card" @submit.prevent="guardarCambios">
      <h2 class="card-title">Editar área</h2>

      <div class="form-row">
        <label class="field">
          <span>Nombre</span>
          <input v-model="editNombre" required />
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

    <!-- Tabla de áreas -->
    <div v-if="store.cargando" class="card">Cargando…</div>

    <div v-else-if="store.areas.length === 0" class="card">
      No hay áreas registradas.
    </div>

    <table v-else class="table">
      <thead>
        <tr>
          <th>Nombre</th>
          <th>Estado</th>
          <th v-if="authStore.isAdmin" class="th-acciones">Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="a in store.areas" :key="a.id">
          <td>{{ a.nombre }}</td>
          <td>
            <span class="badge" :class="a.activa ? 'badge-activo' : 'badge-inactivo'">
              {{ a.activa ? 'Activa' : 'Inactiva' }}
            </span>
          </td>
          <td v-if="authStore.isAdmin" class="td-acciones">
            <button
              class="btn btn-sm"
              :class="areaExpandida === a.id ? 'btn-outline-dark' : 'btn-outline'"
              @click="toggleCélulas(a.id)"
            >
              {{ areaExpandida === a.id ? 'Ocultar células' : 'Células' }}
            </button>
            <button class="btn btn-sm btn-secondary" @click="iniciarEdicion(a)">
              Editar
            </button>
            <button
              class="btn btn-sm"
              :class="a.activa ? 'btn-danger' : 'btn-success'"
              @click="toggleEstadoArea(a)"
            >
              {{ a.activa ? 'Desactivar' : 'Activar' }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Sección de células para el área expandida -->
    <div v-if="areaExpandida !== null && authStore.isAdmin" class="celulas-section">
      <h2 class="section-title">Células</h2>

      <!-- Agregar célula -->
      <form class="card" @submit.prevent="agregarCelula">
        <h3 class="card-title">Agregar célula</h3>

        <div class="form-row">
          <label class="field field-sm">
            <span>Número</span>
            <input
              v-model.number="nuevaCelulaNumero"
              type="number"
              min="1"
              required
            />
          </label>

          <div class="field field-btn">
            <button class="btn btn-primary" type="submit" :disabled="creandoCelula">
              {{ creandoCelula ? 'Agregando…' : 'Agregar' }}
            </button>
          </div>
        </div>
      </form>

      <!-- Editar célula -->
      <form v-if="celulaEditando" class="card" @submit.prevent="guardarCambiosCelula">
        <h3 class="card-title">Editar célula</h3>

        <div class="form-row">
          <label class="field field-sm">
            <span>Número</span>
            <input
              v-model.number="celulaEditNumero"
              type="number"
              min="1"
              required
            />
          </label>

          <div class="field field-btn">
            <button class="btn btn-primary" type="submit" :disabled="guardandoCelula">
              {{ guardandoCelula ? 'Guardando…' : 'Actualizar' }}
            </button>
            <button
              class="btn btn-secondary"
              type="button"
              @click="cancelarEdicionCelula"
            >
              Cancelar
            </button>
          </div>
        </div>
      </form>

      <!-- Tabla de células -->
      <div v-if="store.cargandoCelulas" class="card">Cargando células…</div>

      <div v-else-if="store.celulas.length === 0" class="card">
        No hay células registradas en esta área.
      </div>

      <table v-else class="table">
        <thead>
          <tr>
            <th>Número</th>
            <th>Estado</th>
            <th class="th-acciones">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in store.celulas" :key="c.id">
            <td>{{ c.numero }}</td>
            <td>
              <span class="badge" :class="c.activa ? 'badge-activo' : 'badge-inactivo'">
                {{ c.activa ? 'Activa' : 'Inactiva' }}
              </span>
            </td>
            <td class="td-acciones">
              <button
                class="btn btn-sm btn-secondary"
                @click="iniciarEdicionCelula(c)"
              >
                Editar
              </button>
              <button
                class="btn btn-sm"
                :class="c.activa ? 'btn-danger' : 'btn-success'"
                @click="toggleEstadoCelula(c)"
              >
                {{ c.activa ? 'Desactivar' : 'Activar' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
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

/* ——— Sección de células ——— */
.celulas-section {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 2px solid #e2e8f0;
}

.section-title {
  margin: 0 0 1rem;
  font-size: 1.125rem;
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
  flex: 1 1 200px;
}

.field span {
  font-size: 0.8rem;
  color: #475569;
  font-weight: 500;
}

.field input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.field input:focus {
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

.btn-outline {
  background: transparent;
  color: #475569;
  border: 1px solid #cbd5e1;
  padding: 0.25rem 0.75rem;
}

.btn-outline:hover {
  background: #f1f5f9;
}

.btn-outline-dark {
  background: #1e293b;
  color: #fff;
  border: 1px solid #1e293b;
  padding: 0.25rem 0.75rem;
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

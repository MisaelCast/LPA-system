<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAreasStore } from '@/stores/areas'
import { useAuthStore } from '@/stores/auth'
import type { Area } from '@/types/area'

const store = useAreasStore()
const authStore = useAuthStore()

/* --- Formulario compacto de creación --- */
const formNombre = ref('')
const formCelulas = ref('')
const formGuardando = ref(false)

/* --- Edición inline de área --- */
const areaEditandoId = ref<number | null>(null)
const areaEditNombre = ref('')
const areaEditGuardando = ref(false)

/* --- Edición inline de célula --- */
const celulaEditandoId = ref<number | null>(null)
const celulaEditNumero = ref<number | null>(null)
const celulaEditGuardando = ref(false)

/* --- Agregar célula inline --- */
const areaAgregandoCelulaId = ref<number | null>(null)
const nuevaCelulaNumero = ref<number | null>(null)
const celulaAgregando = ref(false)

/* --- Mensajes --- */
const mensaje = ref('')
const error = ref('')

onMounted(async () => {
  await store.cargarAreas()
  if (store.areas.length > 0) {
    await store.cargarTodasLasCelulas(store.areas.map((a) => a.id))
  }
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

function parsearCelulas(raw: string): number[] {
  return raw
    .split(',')
    .map((n) => Number(n.trim()))
    .filter((n) => Number.isInteger(n) && n > 0)
}

/* ——— Crear área + células ——— */
async function handleCrear() {
  mensaje.value = ''
  error.value = ''
  formGuardando.value = true

  try {
    const area = await store.crear({ nombre: formNombre.value, activa: true })
    const numeros = parsearCelulas(formCelulas.value)

    for (const numero of numeros) {
      try {
        await store.crearCelulaEnArea(area.id, { numero, activa: true })
      } catch (err: unknown) {
        mostrarError(`agregar la célula ${numero}`, err)
      }
    }
    await store.cargarCelulas(area.id)
    mensaje.value = 'Área creada correctamente.'
    formNombre.value = ''
    formCelulas.value = ''
  } catch (err: unknown) {
    mostrarError('crear el área', err)
  } finally {
    formGuardando.value = false
  }
}

/* ——— Editar área ——— */
function iniciarEdicion(a: Area) {
  areaEditandoId.value = a.id
  areaEditNombre.value = a.nombre
}

function cancelarEdicionArea() {
  areaEditandoId.value = null
  areaEditNombre.value = ''
}

async function guardarEdicionArea() {
  if (!areaEditandoId.value) return
  error.value = ''
  areaEditGuardando.value = true

  try {
    await store.actualizar(areaEditandoId.value, { nombre: areaEditNombre.value })
    mensaje.value = 'Área actualizada correctamente.'
    areaEditandoId.value = null
    areaEditNombre.value = ''
  } catch (err: unknown) {
    mostrarError('actualizar el área', err)
  } finally {
    areaEditGuardando.value = false
  }
}

/* ——— Activar/Desactivar área ——— */
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

/* ——— Agregar célula inline ——— */
function mostrarInputCelula(areaId: number) {
  areaAgregandoCelulaId.value = areaId
  nuevaCelulaNumero.value = null
  error.value = ''
}

function cancelarAgregarCelula() {
  areaAgregandoCelulaId.value = null
  nuevaCelulaNumero.value = null
}

async function confirmarAgregarCelula() {
  if (!areaAgregandoCelulaId.value || !nuevaCelulaNumero.value) return
  error.value = ''
  celulaAgregando.value = true

  try {
    await store.crearCelulaEnArea(areaAgregandoCelulaId.value, {
      numero: nuevaCelulaNumero.value,
      activa: true,
    })
    mensaje.value = 'Célula agregada correctamente.'
    areaAgregandoCelulaId.value = null
    nuevaCelulaNumero.value = null
  } catch (err: unknown) {
    mostrarError('agregar la célula', err)
  } finally {
    celulaAgregando.value = false
  }
}

/* ——— Editar célula inline ——— */
function iniciarEdicionCelula(celulaId: number, numeroActual: number) {
  celulaEditandoId.value = celulaId
  celulaEditNumero.value = numeroActual
  error.value = ''
}

function cancelarEdicionCelula() {
  celulaEditandoId.value = null
  celulaEditNumero.value = null
}

async function guardarEdicionCelula(areaId: number) {
  if (!celulaEditandoId.value || !celulaEditNumero.value) return
  error.value = ''
  celulaEditGuardando.value = true

  try {
    await store.actualizarCelulaEnArea(celulaEditandoId.value, areaId, {
      numero: celulaEditNumero.value,
    })
    mensaje.value = 'Célula actualizada correctamente.'
    celulaEditandoId.value = null
    celulaEditNumero.value = null
  } catch (err: unknown) {
    mostrarError('actualizar la célula', err)
  } finally {
    celulaEditGuardando.value = false
  }
}

/* ——— Activar/Desactivar célula ——— */
async function toggleEstadoCelula(celulaId: number, areaId: number, activa: boolean) {
  error.value = ''

  try {
    await store.cambiarEstadoCelulaEnArea(celulaId, areaId, !activa)
    const estado = activa ? 'desactivada' : 'activada'
    mensaje.value = `Célula ${estado} correctamente.`
  } catch (err: unknown) {
    mostrarError('cambiar el estado de la célula', err)
  }
}
</script>

<template>
  <div class="page">
    <h1>Áreas y células</h1>

    <p v-if="mensaje" class="msg msg-ok">{{ mensaje }}</p>
    <p v-if="error" class="msg msg-err">{{ error }}</p>

    <!-- Formulario compacto -->
    <form v-if="authStore.isAdmin" class="bar" @submit.prevent="handleCrear">
      <div class="bar-fields">
        <label class="bar-field bar-field--name">
          <span>Nombre del área</span>
          <input v-model="formNombre" placeholder="Ej: Ensamble Final" required />
        </label>
        <label class="bar-field bar-field--cells">
          <span>Células</span>
          <input
            v-model="formCelulas"
            placeholder="1,2,3,4"
            title="Números de célula separados por coma"
          />
        </label>
      </div>
      <button class="btn btn-dark" type="submit" :disabled="formGuardando">
        {{ formGuardando ? 'Guardando…' : 'Guardar área' }}
      </button>
    </form>

    <div v-if="store.cargando" class="msg msg-info">Cargando…</div>

    <div v-else-if="store.areas.length === 0" class="msg msg-info">
      No hay áreas registradas.
    </div>

    <!-- Tabla única -->
    <table v-else class="table">
      <thead>
        <tr>
          <th class="col-area">Área</th>
          <th class="col-estado">Estado</th>
          <th class="col-celulas">Células</th>
          <th v-if="authStore.isAdmin" class="col-acciones">Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="a in store.areas"
          :key="a.id"
          :class="{ 'row-inactiva': !a.activa }"
        >
          <!-- Nombre del área o input de edición -->
          <td class="col-area">
            <template v-if="areaEditandoId === a.id">
              <input
                v-model="areaEditNombre"
                class="inline-input"
                @keyup.escape="cancelarEdicionArea"
                @keyup.enter="guardarEdicionArea"
              />
              <span class="inline-actions">
                <button
                  class="chip-btn chip-btn--ok"
                  :disabled="areaEditGuardando"
                  @click="guardarEdicionArea"
                >
                  ✓
                </button>
                <button class="chip-btn chip-btn--cancel" @click="cancelarEdicionArea">
                  ✕
                </button>
              </span>
            </template>
            <template v-else>
              {{ a.nombre }}
            </template>
          </td>

          <!-- Estado -->
          <td class="col-estado">
            <span class="badge" :class="a.activa ? 'badge-on' : 'badge-off'">
              {{ a.activa ? 'Activa' : 'Inactiva' }}
            </span>
          </td>

          <!-- Células -->
          <td class="col-celulas">
            <div class="chips">
              <template
                v-for="c in store.celulasDe(a.id)"
                :key="c.id"
              >
                <!-- Chip en edición -->
                <span
                  v-if="celulaEditandoId === c.id"
                  class="chip chip-editing"
                >
                  <input
                    v-model.number="celulaEditNumero"
                    type="number"
                    min="1"
                    class="chip-input"
                    @keyup.escape="cancelarEdicionCelula"
                    @keyup.enter="guardarEdicionCelula(a.id)"
                  />
                  <button
                    class="chip-btn chip-btn--ok"
                    :disabled="celulaEditGuardando"
                    @click="guardarEdicionCelula(a.id)"
                  >
                    ✓
                  </button>
                  <button class="chip-btn chip-btn--cancel" @click="cancelarEdicionCelula">
                    ✕
                  </button>
                </span>

                <!-- Chip normal -->
                <span
                  v-else
                  class="chip"
                  :class="{ 'chip-off': !c.activa }"
                >
                  <span class="chip-num">{{ c.numero }}</span>
                  <button
                    v-if="authStore.isAdmin"
                    class="chip-btn"
                    title="Editar número"
                    @click="iniciarEdicionCelula(c.id, c.numero)"
                  >
                    ✏️
                  </button>
                  <button
                    v-if="authStore.isAdmin"
                    class="chip-btn"
                    :title="c.activa ? 'Desactivar' : 'Activar'"
                    @click="toggleEstadoCelula(c.id, a.id, c.activa)"
                  >
                    {{ c.activa ? '✕' : '↺' }}
                  </button>
                </span>
              </template>

              <!-- Input para agregar nueva célula -->
              <span
                v-if="areaAgregandoCelulaId === a.id"
                class="chip chip-editing"
              >
                <input
                  v-model.number="nuevaCelulaNumero"
                  type="number"
                  min="1"
                  placeholder="N°"
                  class="chip-input"
                  @keyup.escape="cancelarAgregarCelula"
                  @keyup.enter="confirmarAgregarCelula"
                />
                <button
                  class="chip-btn chip-btn--ok"
                  :disabled="celulaAgregando"
                  @click="confirmarAgregarCelula"
                >
                  ✓
                </button>
                <button class="chip-btn chip-btn--cancel" @click="cancelarAgregarCelula">
                  ✕
                </button>
              </span>

              <!-- Botón Agregar célula -->
              <button
                v-if="authStore.isAdmin && areaAgregandoCelulaId !== a.id"
                class="chip chip-add"
                @click="mostrarInputCelula(a.id)"
              >
                + Agregar
              </button>
            </div>
          </td>

          <!-- Acciones -->
          <td v-if="authStore.isAdmin" class="col-acciones">
            <template v-if="areaEditandoId === a.id">
              <!-- ya se muestran los botones en el td de nombre -->
            </template>
            <template v-else>
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
            </template>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
/* --- Layout --- */
.page {
  max-width: 1400px;
}

h1 {
  margin: 0 0 1rem;
  font-size: 1.25rem;
  color: #1e293b;
}

/* --- Mensajes --- */
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

/* --- Barra de formulario --- */
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
  flex: 1 1 250px;
}

.bar-field--cells {
  flex: 0 0 160px;
}

/* --- Tabla --- */
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

.col-area {
  width: 25%;
}

.col-estado {
  width: 10%;
}

.col-celulas {
  width: 47%;
}

.col-acciones {
  width: 18%;
  text-align: right;
  white-space: nowrap;
}

/* --- Chips --- */
.chips {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  flex-wrap: wrap;
  min-height: 2rem;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 0.15rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 0.25rem;
  padding: 0.125rem 0.15rem 0.125rem 0.4rem;
  font-size: 0.8rem;
  font-weight: 500;
  color: #334155;
  white-space: nowrap;
  user-select: none;
}

.chip-off {
  opacity: 0.5;
  text-decoration: line-through;
}

.chip-num {
  min-width: 1rem;
  text-align: center;
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

.chip-add {
  cursor: pointer;
  background: transparent;
  border: 1px dashed #cbd5e1;
  color: #94a3b8;
  font-size: 0.75rem;
  padding: 0.15rem 0.5rem;
  transition: color 0.15s, border-color 0.15s;
}

.chip-add:hover {
  color: #475569;
  border-color: #94a3b8;
}

.chip-editing {
  background: #eff6ff;
  border-color: #93c5fd;
  gap: 0.15rem;
  padding: 0.125rem 0.15rem;
}

.chip-input {
  width: 2.5rem;
  padding: 0.15rem 0.25rem;
  border: 1px solid #93c5fd;
  border-radius: 0.15rem;
  font-size: 0.8rem;
  text-align: center;
  background: #fff;
  -moz-appearance: textfield;
}

.chip-input::-webkit-inner-spin-button,
.chip-input::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.chip-input:focus {
  outline: none;
  border-color: #3b82f6;
}

/* --- Input inline en celda --- */
.inline-input {
  width: calc(100% - 3rem);
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

.inline-actions {
  display: inline-flex;
  gap: 0.15rem;
  margin-left: 0.25rem;
  vertical-align: middle;
}

/* --- Badges --- */
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

/* --- Botones --- */
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

.col-acciones {
  display: flex;
  gap: 0.35rem;
  justify-content: flex-end;
}
</style>

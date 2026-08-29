<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAuditoriasStore } from '@/stores/auditorias'
import { useCriteriosStore } from '@/stores/criterios'
import { useAuthStore } from '@/stores/auth'
import { useAreasStore } from '@/stores/areas'
import { useCapasStore } from '@/stores/capas'
import { useFrecuenciasStore } from '@/stores/frecuencias'
import type { Auditoria } from '@/types/auditoria'

const auditoriaStore = useAuditoriasStore()
const criterioStore = useCriteriosStore()
const authStore = useAuthStore()
const areasStore = useAreasStore()
const capasStore = useCapasStore()
const frecuenciasStore = useFrecuenciasStore()

/* --- Creacion --- */
const formNombre = ref('')
const formDescripcion = ref('')
const formAreaId = ref<number | null>(null)
const formCapaId = ref<number | null>(null)
const formFrecuenciaId = ref<number | null>(null)
const formGuardando = ref(false)

/* --- Edicion de auditoria --- */
const editAuditoriaId = ref<number | null>(null)
const editNombre = ref('')
const editDescripcion = ref('')
const editAreaId = ref<number | null>(null)
const editCapaId = ref<number | null>(null)
const editFrecuenciaId = ref<number | null>(null)
const editGuardando = ref(false)

/* --- Criterios expandidos --- */
const auditoriaExpandidaId = ref<number | null>(null)

/* --- Edicion de criterio --- */
const criterioEditId = ref<number | null>(null)
const criterioEditDesc = ref('')
const criterioEditOrden = ref<number>(1)
const criterioEditGuardando = ref(false)

/* --- Agregar criterio --- */
const nuevoCriterioDesc = ref('')
const nuevoCriterioOrden = ref<number>(1)
const criterioAgregando = ref(false)

/* --- Mensajes --- */
const mensaje = ref('')
const error = ref('')

onMounted(async () => {
  await Promise.all([
    auditoriaStore.cargarAuditorias(),
    areasStore.cargarAreas(),
    capasStore.cargarCapas(),
    frecuenciasStore.cargarFrecuencias(),
  ])
  if (auditoriaStore.auditorias.length > 0) {
    await criterioStore.cargarTodosLosCriterios(
      auditoriaStore.auditorias.map((a) => a.id),
    )
  }
})

function mostrarError(prefix: string, err: unknown) {
  if (err && typeof err === 'object' && 'response' in err) {
    const axiosErr = err as {
      response: { status: number; data?: { detail?: string } }
    }
    if (axiosErr.response.status === 403) {
      error.value = 'No tiene permisos para realizar esta accion.'
    } else {
      error.value =
        axiosErr.response.data?.detail || `Error al ${prefix}.`
    }
  } else {
    error.value = `Error al ${prefix}.`
  }
}

/* --- Crear --- */
async function handleCrear() {
  mensaje.value = ''
  error.value = ''

  if (
    !formNombre.value ||
    !formAreaId.value ||
    !formCapaId.value ||
    !formFrecuenciaId.value
  ) {
    error.value = 'Complete todos los campos obligatorios.'
    return
  }

  formGuardando.value = true
  try {
    await auditoriaStore.crear({
      nombre: formNombre.value,
      descripcion: formDescripcion.value || undefined,
      activa: true,
      area_id: formAreaId.value,
      capa_id: formCapaId.value,
      frecuencia_id: formFrecuenciaId.value,
    })
    mensaje.value = 'Auditoria creada correctamente.'
    formNombre.value = ''
    formDescripcion.value = ''
    formAreaId.value = null
    formCapaId.value = null
    formFrecuenciaId.value = null
  } catch (err: unknown) {
    mostrarError('crear la auditoria', err)
  } finally {
    formGuardando.value = false
  }
}

/* --- Editar --- */
function iniciarEdicion(a: Auditoria) {
  editAuditoriaId.value = a.id
  editNombre.value = a.nombre
  editDescripcion.value = a.descripcion || ''
  editAreaId.value = a.area_id
  editCapaId.value = a.capa_id
  editFrecuenciaId.value = a.frecuencia_id
}

function cancelarEdicion() {
  editAuditoriaId.value = null
}

async function guardarEdicion() {
  if (!editAuditoriaId.value) return
  error.value = ''
  editGuardando.value = true

  try {
    await auditoriaStore.actualizar(editAuditoriaId.value, {
      nombre: editNombre.value,
      descripcion: editDescripcion.value || undefined,
      area_id: editAreaId.value ?? undefined,
      capa_id: editCapaId.value ?? undefined,
      frecuencia_id: editFrecuenciaId.value ?? undefined,
    })
    mensaje.value = 'Auditoria actualizada correctamente.'
    editAuditoriaId.value = null
  } catch (err: unknown) {
    mostrarError('actualizar la auditoria', err)
  } finally {
    editGuardando.value = false
  }
}

/* --- Eliminar --- */
async function eliminarAuditoria(a: Auditoria) {
  if (!window.confirm(`¿Está seguro de que desea eliminar la auditoría "${a.nombre}"?\n\nEsta acción no se puede deshacer.`)) return
  mensaje.value = ''
  error.value = ''

  try {
    await auditoriaStore.eliminar(a.id)
    mensaje.value = 'Auditoria eliminada correctamente.'
  } catch (err: unknown) {
    mostrarError('eliminar la auditoria', err)
  }
}

/* --- Expandir criterios --- */
function toggleCriterios(auditoriaId: number) {
  if (auditoriaExpandidaId.value === auditoriaId) {
    auditoriaExpandidaId.value = null
  } else {
    auditoriaExpandidaId.value = auditoriaId
    criterioStore.cargarCriterios(auditoriaId)
    nuevoCriterioDesc.value = ''
    nuevoCriterioOrden.value =
      Math.max(
        0,
        ...criterioStore.criteriosDe(auditoriaId).map((c) => c.orden),
      ) + 1
  }
}

/* --- Criterios: crear --- */
async function handleCrearCriterio(auditoriaId: number) {
  if (!nuevoCriterioDesc.value) return
  error.value = ''
  criterioAgregando.value = true

  try {
    await criterioStore.crearEnAuditoria(auditoriaId, {
      descripcion: nuevoCriterioDesc.value,
      orden: nuevoCriterioOrden.value || 1,
      activo: true,
    })
    mensaje.value = 'Criterio agregado correctamente.'
    nuevoCriterioDesc.value = ''
    nuevoCriterioOrden.value =
      Math.max(
        0,
        ...criterioStore.criteriosDe(auditoriaId).map((c) => c.orden),
      ) + 1
  } catch (err: unknown) {
    mostrarError('agregar el criterio', err)
  } finally {
    criterioAgregando.value = false
  }
}

/* --- Criterios: editar --- */
function iniciarEdicionCriterio(c: { id: number; descripcion: string; orden: number }) {
  criterioEditId.value = c.id
  criterioEditDesc.value = c.descripcion
  criterioEditOrden.value = c.orden
}

function cancelarEdicionCriterio() {
  criterioEditId.value = null
}

async function guardarEdicionCriterio(auditoriaId: number) {
  if (!criterioEditId.value) return
  error.value = ''
  criterioEditGuardando.value = true

  try {
    await criterioStore.actualizar(auditoriaId, criterioEditId.value, {
      descripcion: criterioEditDesc.value,
      orden: criterioEditOrden.value,
    })
    mensaje.value = 'Criterio actualizado correctamente.'
    criterioEditId.value = null
  } catch (err: unknown) {
    mostrarError('actualizar el criterio', err)
  } finally {
    criterioEditGuardando.value = false
  }
}

/* --- Criterios: estado --- */
async function toggleEstadoCriterio(auditoriaId: number, c: { id: number; activo: boolean }) {
  error.value = ''
  try {
    await criterioStore.cambiarEstado(auditoriaId, c.id, !c.activo)
    const estado = c.activo ? 'desactivado' : 'activado'
    mensaje.value = `Criterio ${estado} correctamente.`
  } catch (err: unknown) {
    mostrarError('cambiar el estado del criterio', err)
  }
}
</script>

<template>
  <div class="page">
    <h1>Auditorias</h1>

    <p v-if="mensaje" class="msg msg-ok">{{ mensaje }}</p>
    <p v-if="error" class="msg msg-err">{{ error }}</p>

    <!-- Formulario de creacion -->
    <form v-if="authStore.isAdmin" class="bar" @submit.prevent="handleCrear">
      <div class="bar-fields">
        <label class="bar-field bar-field--name">
          <span>Nombre *</span>
          <input v-model="formNombre" placeholder="Ej: Auditoria de Proceso" required />
        </label>
        <label class="bar-field bar-field--desc">
          <span>Descripcion</span>
          <input v-model="formDescripcion" placeholder="Opcional" />
        </label>
        <label class="bar-field bar-field--select">
          <span>Area *</span>
          <select v-model.number="formAreaId" required>
            <option :value="null" disabled>Seleccione</option>
            <option v-for="a in areasStore.areas" :key="a.id" :value="a.id">
              {{ a.nombre }}
            </option>
          </select>
        </label>
        <label class="bar-field bar-field--select">
          <span>Capa *</span>
          <select v-model.number="formCapaId" required>
            <option :value="null" disabled>Seleccione</option>
            <option v-for="c in capasStore.capas" :key="c.id" :value="c.id">
              {{ c.nombre }}
            </option>
          </select>
        </label>
        <label class="bar-field bar-field--select">
          <span>Frecuencia *</span>
          <select v-model.number="formFrecuenciaId" required>
            <option :value="null" disabled>Seleccione</option>
            <option v-for="f in frecuenciasStore.frecuencias" :key="f.id" :value="f.id">
              {{ f.nombre }}
            </option>
          </select>
        </label>
      </div>
      <button class="btn btn-dark" type="submit" :disabled="formGuardando">
        {{ formGuardando ? 'Guardando...' : 'Crear auditoria' }}
      </button>
    </form>

    <div v-if="auditoriaStore.cargando" class="msg msg-info">Cargando...</div>

    <div v-else-if="auditoriaStore.auditorias.length === 0" class="msg msg-info">
      No hay auditorias registradas.
    </div>

    <template v-else>
      <table class="table">
        <thead>
          <tr>
            <th class="col-nombre">Auditoria</th>
            <th class="col-area">Area</th>
            <th class="col-capa">Capa</th>
            <th class="col-frec">Frecuencia</th>
            <th class="col-estado">Estado</th>
            <th v-if="authStore.isAdmin" class="col-acciones">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="a in auditoriaStore.auditorias" :key="a.id">
            <tr :class="{ 'row-inactiva': !a.activa }">
              <!-- Nombre / Edicion -->
              <td class="col-nombre">
                <template v-if="editAuditoriaId === a.id">
                  <input
                    v-model="editNombre"
                    class="inline-input"
                    @keyup.escape="cancelarEdicion"
                    @keyup.enter="guardarEdicion"
                  />
                </template>
                <template v-else>
                  <button
                    class="lnk"
                    :class="{ 'lnk-open': auditoriaExpandidaId === a.id }"
                    @click="toggleCriterios(a.id)"
                  >
                    {{ a.nombre }}
                  </button>
                  <span v-if="auditoriaExpandidaId === a.id" class="lnk-arrow">&#9660;</span>
                </template>
              </td>
              <!-- Area -->
              <td class="col-area">
                <template v-if="editAuditoriaId === a.id">
                  <select v-model.number="editAreaId" class="inline-select">
                    <option :value="null">Sin area</option>
                    <option v-for="ar in areasStore.areas" :key="ar.id" :value="ar.id">
                      {{ ar.nombre }}
                    </option>
                  </select>
                </template>
                <template v-else>
                  {{ a.area_nombre || '—' }}
                </template>
              </td>
              <!-- Capa -->
              <td class="col-capa">
                <template v-if="editAuditoriaId === a.id">
                  <select v-model.number="editCapaId" class="inline-select">
                    <option v-for="c in capasStore.capas" :key="c.id" :value="c.id">
                      {{ c.nombre }}
                    </option>
                  </select>
                </template>
                <template v-else>
                  {{ a.capa_nombre }}
                </template>
              </td>
              <!-- Frecuencia -->
              <td class="col-frec">
                <template v-if="editAuditoriaId === a.id">
                  <select v-model.number="editFrecuenciaId" class="inline-select">
                    <option v-for="f in frecuenciasStore.frecuencias" :key="f.id" :value="f.id">
                      {{ f.nombre }}
                    </option>
                  </select>
                </template>
                <template v-else>
                  {{ a.frecuencia_nombre }}
                </template>
              </td>
              <!-- Estado -->
              <td class="col-estado">
                <span class="badge" :class="a.activa ? 'badge-on' : 'badge-off'">
                  {{ a.activa ? 'Activa' : 'Inactiva' }}
                </span>
              </td>
              <!-- Acciones -->
              <td v-if="authStore.isAdmin" class="col-acciones">
                <template v-if="editAuditoriaId === a.id">
                  <button
                    class="chip-btn chip-btn--ok"
                    :disabled="editGuardando"
                    @click="guardarEdicion"
                  >&#10003;</button>
                  <button class="chip-btn chip-btn--cancel" @click="cancelarEdicion">&#10005;</button>
                </template>
                <template v-else>
                  <button class="btn btn-sm btn-secondary" @click="iniciarEdicion(a)">Editar</button>
                  <button class="btn btn-sm btn-danger" @click="eliminarAuditoria(a)">
                    Eliminar
                  </button>
                </template>
              </td>
            </tr>

            <!-- Seccion expandible: criterios -->
            <tr v-if="auditoriaExpandidaId === a.id" class="row-criterios">
              <td :colspan="authStore.isAdmin ? 6 : 5">
                <div class="criterios-panel">
                  <div class="criterios-header">Criterios</div>

                  <table class="criterios-table" v-if="criterioStore.criteriosDe(a.id).length > 0">
                    <thead>
                      <tr>
                        <th class="ccol-ord">#</th>
                        <th class="ccol-desc">Descripcion</th>
                        <th class="ccol-estado">Estado</th>
                        <th v-if="authStore.isAdmin" class="ccol-acc">Acciones</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="c in criterioStore.criteriosDe(a.id)"
                        :key="c.id"
                        :class="{ 'row-inactiva': !c.activo }"
                      >
                        <td class="ccol-ord">
                          <template v-if="criterioEditId === c.id">
                            <input
                              v-model.number="criterioEditOrden"
                              type="number"
                              min="1"
                              class="criterio-input-num"
                            />
                          </template>
                          <template v-else>
                            {{ c.orden }}
                          </template>
                        </td>
                        <td class="ccol-desc">
                          <template v-if="criterioEditId === c.id">
                            <input
                              v-model="criterioEditDesc"
                              class="criterio-input"
                              @keyup.escape="cancelarEdicionCriterio"
                              @keyup.enter="guardarEdicionCriterio(a.id)"
                            />
                          </template>
                          <template v-else>
                            {{ c.descripcion }}
                          </template>
                        </td>
                        <td class="ccol-estado">
                          <span class="badge" :class="c.activo ? 'badge-on' : 'badge-off'">
                            {{ c.activo ? 'Activo' : 'Inactivo' }}
                          </span>
                        </td>
                        <td v-if="authStore.isAdmin" class="ccol-acc">
                          <template v-if="criterioEditId === c.id">
                            <button
                              class="chip-btn chip-btn--ok"
                              :disabled="criterioEditGuardando"
                              @click="guardarEdicionCriterio(a.id)"
                            >&#10003;</button>
                            <button class="chip-btn chip-btn--cancel" @click="cancelarEdicionCriterio">&#10005;</button>
                          </template>
                          <template v-else>
                            <button class="btn btn-sm btn-secondary" @click="iniciarEdicionCriterio(c)">Editar</button>
                            <button
                              class="btn btn-xs"
                              :class="c.activo ? 'btn-danger' : 'btn-success'"
                              @click="toggleEstadoCriterio(a.id, c)"
                            >
                              {{ c.activo ? 'Desact.' : 'Activar' }}
                            </button>
                          </template>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <div v-else class="msg msg-info" style="margin-top:0.5rem">Sin criterios.</div>

                  <!-- Agregar criterio -->
                  <div v-if="authStore.isAdmin" class="criterio-add-bar">
                    <input
                      v-model="nuevoCriterioDesc"
                      placeholder="Nuevo criterio"
                      class="criterio-input criterio-add-input"
                      @keyup.enter="handleCrearCriterio(a.id)"
                    />
                    <input
                      v-model.number="nuevoCriterioOrden"
                      type="number"
                      min="1"
                      class="criterio-input-num"
                      title="Orden"
                    />
                    <button
                      class="btn btn-dark btn-xs"
                      :disabled="criterioAgregando"
                      @click="handleCrearCriterio(a.id)"
                    >
                      + Agregar
                    </button>
                  </div>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </template>
  </div>
</template>

<style scoped>
.page { max-width: 1300px; }

h1 { margin: 0 0 1rem; font-size: 1.25rem; color: #1e293b; }

.msg { padding: 0.5rem 0.75rem; border-radius: 0.375rem; font-size: 0.8rem; margin-bottom: 0.75rem; }
.msg-ok { background: #f0fdf4; color: #16a34a; }
.msg-err { background: #fef2f2; color: #dc2626; }
.msg-info { background: #f8fafc; color: #64748b; }

/* --- Barra de formulario --- */
.bar {
  display: flex; align-items: flex-end; gap: 0.75rem;
  background: #fff; border-radius: 0.375rem; box-shadow: 0 1px 2px rgba(0,0,0,0.06);
  padding: 0.75rem 1rem; margin-bottom: 1rem; border: 1px solid #e2e8f0;
}
.bar-fields { display: flex; gap: 0.75rem; flex: 1; flex-wrap: wrap; }
.bar-field { display: flex; flex-direction: column; gap: 0.15rem; min-width: 0; }
.bar-field span { font-size: 0.7rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.025em; }
.bar-field input, .bar-field select {
  padding: 0.4rem 0.6rem; border: 1px solid #e2e8f0; border-radius: 0.25rem; font-size: 0.85rem; min-width: 0;
}
.bar-field input:focus, .bar-field select:focus {
  outline: none; border-color: #3b82f6; box-shadow: 0 0 0 1px #3b82f6;
}
.bar-field--name { flex: 1 1 160px; }
.bar-field--desc { flex: 1.5 1 180px; }
.bar-field--select { flex: 0 0 140px; }

/* --- Tabla principal --- */
.table {
  width: 100%; border-collapse: collapse; background: #fff;
  border-radius: 0.375rem; overflow: hidden;
  box-shadow: 0 1px 2px rgba(0,0,0,0.06); border: 1px solid #e2e8f0;
}
th {
  text-align: left; padding: 0.5rem 0.75rem; background: #f8fafc;
  color: #64748b; font-size: 0.72rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.025em; border-bottom: 1px solid #e2e8f0;
}
td { padding: 0.5rem 0.75rem; border-bottom: 1px solid #f1f5f9; font-size: 0.85rem; color: #334155; vertical-align: middle; }
tr:last-child td { border-bottom: none; }
.row-inactiva { opacity: 0.5; }

.col-nombre { width: 22%; }
.col-area { width: 15%; }
.col-capa { width: 12%; }
.col-frec { width: 12%; }
.col-estado { width: 10%; }
.col-acciones { width: 29%; text-align: right; white-space: nowrap; }

.col-acciones { display: flex; gap: 0.35rem; justify-content: flex-end; }

/* --- Link expandible --- */
.lnk {
  background: none; border: none; color: #1d4ed8; cursor: pointer; font-size: 0.85rem; padding: 0; text-align: left;
  text-decoration: none;
}
.lnk:hover { text-decoration: underline; }
.lnk-open { font-weight: 600; }
.lnk-arrow { font-size: 0.65rem; color: #1d4ed8; margin-left: 0.25rem; }

/* --- Inline editing --- */
.inline-input {
  width: calc(100% - 0.5rem); padding: 0.35rem 0.5rem;
  border: 1px solid #93c5fd; border-radius: 0.25rem; font-size: 0.85rem; background: #eff6ff;
}
.inline-input:focus { outline: none; border-color: #3b82f6; }
.inline-select {
  padding: 0.35rem 0.5rem; border: 1px solid #93c5fd; border-radius: 0.25rem;
  font-size: 0.85rem; background: #eff6ff; max-width: 120px;
}
.inline-select:focus { outline: none; border-color: #3b82f6; }

/* --- Badges --- */
.badge { display: inline-block; padding: 0.125rem 0.45rem; border-radius: 999px; font-size: 0.7rem; font-weight: 600; }
.badge-on { background: #dcfce7; color: #16a34a; }
.badge-off { background: #fee2e2; color: #dc2626; }

/* --- Botones --- */
.btn { border: none; border-radius: 0.25rem; cursor: pointer; font-size: 0.8rem; vertical-align: middle; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-dark { background: #1e293b; color: #fff; padding: 0.45rem 0.9rem; font-size: 0.85rem; white-space: nowrap; border-radius: 0.25rem; flex-shrink: 0; }
.btn-dark:hover { background: #334155; }
.btn-secondary { background: #e2e8f0; color: #334155; padding: 0.3rem 0.6rem; }
.btn-secondary:hover { background: #cbd5e1; }
.btn-sm { padding: 0.25rem 0.6rem; font-size: 0.75rem; }
.btn-xs { padding: 0.15rem 0.4rem; font-size: 0.7rem; }
.btn-danger { background: #fef2f2; color: #dc2626; }
.btn-danger:hover { background: #fee2e2; }
.btn-success { background: #f0fdf4; color: #16a34a; }
.btn-success:hover { background: #dcfce7; }

.chip-btn {
  display: inline-flex; align-items: center; justify-content: center;
  width: 1.1rem; height: 1.1rem; border: none; background: transparent;
  border-radius: 0.15rem; cursor: pointer; font-size: 0.65rem; line-height: 1; padding: 0;
  color: #94a3b8; transition: color 0.15s, background 0.15s;
}
.chip-btn:hover { color: #475569; background: #e2e8f0; }
.chip-btn--ok { color: #16a34a; }
.chip-btn--ok:hover { color: #16a34a; background: #dcfce7; }
.chip-btn--cancel { color: #dc2626; }
.chip-btn--cancel:hover { color: #dc2626; background: #fee2e2; }

/* --- Panel de criterios --- */
.row-criterios td { background: #f8fafc; padding: 0; border-bottom: 1px solid #e2e8f0; }
.criterios-panel { padding: 0.75rem 1rem; }
.criterios-header { font-size: 0.75rem; font-weight: 600; color: #64748b; text-transform: uppercase; margin-bottom: 0.5rem; }
.criterios-table { width: 100%; border-collapse: collapse; }
.criterios-table th {
  padding: 0.3rem 0.5rem; font-size: 0.65rem; background: #f1f5f9;
  color: #64748b; text-transform: uppercase; letter-spacing: 0.025em;
  border-bottom: 1px solid #e2e8f0; text-align: left;
}
.criterios-table td { padding: 0.35rem 0.5rem; border-bottom: 1px solid #f1f5f9; font-size: 0.8rem; }
.criterios-table tr:last-child td { border-bottom: none; }
.ccol-ord { width: 40px; text-align: center; }
.ccol-desc { width: auto; }
.ccol-estado { width: 80px; }
.ccol-acc { width: 120px; text-align: right; white-space: nowrap; }
.ccol-acc { display: flex; gap: 0.25rem; justify-content: flex-end; }

.criterio-input {
  width: calc(100% - 0.5rem); padding: 0.25rem 0.4rem;
  border: 1px solid #e2e8f0; border-radius: 0.2rem; font-size: 0.8rem;
}
.criterio-input:focus { outline: none; border-color: #3b82f6; }
.criterio-input-num {
  width: 45px; padding: 0.25rem 0.3rem; text-align: center;
  border: 1px solid #e2e8f0; border-radius: 0.2rem; font-size: 0.8rem;
  -moz-appearance: textfield;
}
.criterio-input-num::-webkit-inner-spin-button,
.criterio-input-num::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
.criterio-input-num:focus { outline: none; border-color: #3b82f6; }

.criterio-add-bar {
  display: flex; align-items: center; gap: 0.4rem; margin-top: 0.5rem; padding-top: 0.5rem;
  border-top: 1px dashed #e2e8f0;
}
.criterio-add-input { flex: 1; }
</style>

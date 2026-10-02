<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Auditoria } from '@/types/auditoria'
import type { Celula } from '@/types/area'
import type { EjecucionAuditoria, CriterioRespuesta } from '@/types/ejecucion'
import {
  obtenerAuditoriasDisponibles,
  obtenerCelulasDisponibles,
  iniciarEjecucion,
  obtenerEjecucion,
  guardarRespuestas,
  finalizarEjecucion,
} from '@/services/ejecucion.service'
import {
  crearHallazgo,
  actualizarHallazgo,
  eliminarHallazgo,
} from '@/services/hallazgo.service'

const router = useRouter()
const route = useRoute()

const paso = ref<'seleccionar' | 'celulas' | 'ejecutando' | 'terminado'>('seleccionar')
const error = ref('')
const exito = ref('')
const cargando = ref(false)

const auditorias = ref<Auditoria[]>([])
const auditoriaSeleccionada = ref<Auditoria | null>(null)
const celulas = ref<Celula[]>([])
const ejecucion = ref<EjecucionAuditoria | null>(null)

const hallazgosInputs = ref<Record<number, string>>({})
const hallazgosGuardando = ref<Record<number, boolean>>({})
const hallazgosError = ref<Record<number, string>>({})

const criterios = computed(() => ejecucion.value?.criterios || [])
const respondidos = computed(() =>
  criterios.value.filter((c) => c.respuesta_valor !== null).length,
)
const total = computed(() => criterios.value.length)
const finalizada = computed(() => ejecucion.value?.estado === 'finalizada')

async function mostrarError(prefix: string, err: unknown) {
  const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || String(err)
  error.value = `${prefix}: ${msg}`
}

function limpiarMensajes() {
  error.value = ''
  exito.value = ''
}

onMounted(async () => {
  const idParam = route.query.id
  if (idParam) {
    const id = Number(idParam)
    if (Number.isInteger(id)) {
      await cargarEjecucionExistente(id)
      return
    }
  }
  try {
    auditorias.value = await obtenerAuditoriasDisponibles()
  } catch (err) {
    mostrarError('Error al cargar auditorías', err)
  }
})

async function cargarEjecucionExistente(id: number) {
  limpiarMensajes()
  cargando.value = true
  try {
    ejecucion.value = await obtenerEjecucion(id)
    sincronizarBorradorHallazgos()
    paso.value = 'ejecutando'
  } catch (err) {
    mostrarError('Error al cargar la ejecución', err)
    paso.value = 'seleccionar'
  } finally {
    cargando.value = false
  }
}

function seleccionarAuditoria(auditoria: Auditoria) {
  limpiarMensajes()
  auditoriaSeleccionada.value = auditoria
  paso.value = 'celulas'
  cargarCelulas(auditoria.id)
}

async function cargarCelulas(auditoriaId: number) {
  try {
    celulas.value = await obtenerCelulasDisponibles(auditoriaId)
  } catch (err) {
    mostrarError('Error al cargar células', err)
  }
}

async function iniciar(celula: Celula) {
  limpiarMensajes()
  cargando.value = true
  try {
    const ej = await iniciarEjecucion(auditoriaSeleccionada.value!.id, {
      celula_id: celula.id,
    })
    ejecucion.value = ej
    sincronizarBorradorHallazgos()
    paso.value = 'ejecutando'
  } catch (err) {
    mostrarError('Error al iniciar ejecución', err)
  } finally {
    cargando.value = false
  }
}

function sincronizarBorradorHallazgos() {
  if (!ejecucion.value) return
  const merged: Record<number, string> = { ...hallazgosInputs.value }
  for (const c of ejecucion.value.criterios) {
    if (c.hallazgo_descripcion) {
      merged[c.id] = c.hallazgo_descripcion
    }
  }
  hallazgosInputs.value = merged
  hallazgosError.value = {}
  hallazgosGuardando.value = {}
}

async function seleccionarValor(criterio: CriterioRespuesta, valor: string) {
  criterio.respuesta_valor = criterio.respuesta_valor === valor ? null : valor
  if (valor === 'V' && criterio.respuesta_valor === 'V') {
    criterio.respuesta_observaciones = null
    if (criterio.hallazgo_id !== null && !finalizada.value) {
      await quitarHallazgo(criterio)
    }
    return
  }

  if (criterio.respuesta_valor === null && criterio.hallazgo_id !== null) {
    await quitarHallazgo(criterio)
  }
}

async function quitarHallazgo(criterio: CriterioRespuesta) {
  if (criterio.hallazgo_id === null) return
  try {
    await eliminarHallazgo(criterio.hallazgo_id)
    criterio.hallazgo_id = null
    criterio.hallazgo_descripcion = null
    delete hallazgosInputs.value[criterio.id]
    delete hallazgosError.value[criterio.id]
  } catch (err) {
    mostrarError('No se pudo eliminar el hallazgo', err)
  }
}

async function persistirRespuestasPendientes(): Promise<void> {
  if (!ejecucion.value) return
  const respuestas = criterios.value
    .filter((c) => c.respuesta_valor !== null && c.respuesta_id === null)
    .map((c) => ({
      criterio_id: c.id,
      valor: c.respuesta_valor!,
      observaciones: c.respuesta_observaciones || null,
    }))
  if (respuestas.length === 0) return
  ejecucion.value = await guardarRespuestas(ejecucion.value.id, { respuestas })
}

async function guardarHallazgo(criterio: CriterioRespuesta) {
  if (finalizada.value) {
    hallazgosError.value[criterio.id] =
      'La ejecución está finalizada, no se pueden modificar hallazgos.'
    return
  }
  const descripcion = (hallazgosInputs.value[criterio.id] ?? '').trim()
  if (!descripcion) {
    hallazgosError.value[criterio.id] = 'La descripción es obligatoria.'
    return
  }
  hallazgosGuardando.value[criterio.id] = true
  hallazgosError.value[criterio.id] = 'Guardando respuesta, espera un momento…'
  try {
    if (!criterio.respuesta_id) {
      await persistirRespuestasPendientes()
    }
    const crit = criterios.value.find((c) => c.id === criterio.id)
    if (!crit || !crit.respuesta_id) {
      hallazgosError.value[criterio.id] =
        'No se pudo guardar la respuesta. Intenta de nuevo.'
      return
    }
    if (crit.hallazgo_id !== null) {
      const actualizado = await actualizarHallazgo(crit.hallazgo_id, {
        descripcion,
      })
      crit.hallazgo_id = actualizado.id
      crit.hallazgo_descripcion = actualizado.descripcion
    } else {
      const creado = await crearHallazgo(crit.respuesta_id, {
        descripcion,
      })
      crit.hallazgo_id = creado.id
      crit.hallazgo_descripcion = creado.descripcion
      hallazgosInputs.value[crit.id] = creado.descripcion
    }
    hallazgosError.value[crit.id] = ''
    exito.value = 'Hallazgo guardado correctamente.'
  } catch (err) {
    hallazgosError.value[criterio.id] =
      (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
      String(err)
  } finally {
    hallazgosGuardando.value[criterio.id] = false
  }
}

async function guardar() {
  limpiarMensajes()
  cargando.value = true
  try {
    const respuestas = criterios.value
      .filter((c) => c.respuesta_valor !== null)
      .map((c) => ({
        criterio_id: c.id,
        valor: c.respuesta_valor!,
        observaciones: c.respuesta_observaciones || null,
      }))
    ejecucion.value = await guardarRespuestas(ejecucion.value!.id, { respuestas })
    sincronizarBorradorHallazgos()
    for (const c of criterios.value) {
      if (c.respuesta_valor === 'A' || c.respuesta_valor === 'R') {
        const borrador = (hallazgosInputs.value[c.id] ?? '').trim()
        if (borrador && c.hallazgo_id === null) {
          await guardarHallazgo(c)
        }
      }
    }
    exito.value = 'Respuestas guardadas correctamente.'
  } catch (err) {
    mostrarError('Error al guardar', err)
  } finally {
    cargando.value = false
  }
}

async function finalizar() {
  limpiarMensajes()
  if (respondidos.value < total.value) {
    error.value = `Faltan ${total.value - respondidos.value} criterios por responder.`
    return
  }
  cargando.value = true
  try {
    ejecucion.value = await finalizarEjecucion(ejecucion.value!.id)
    paso.value = 'terminado'
    exito.value = 'Auditoría finalizada correctamente.'
  } catch (err) {
    mostrarError('Error al finalizar', err)
  } finally {
    cargando.value = false
  }
}

function mostrarCampoHallazgo(criterio: CriterioRespuesta): boolean {
  return criterio.respuesta_valor === 'A' || criterio.respuesta_valor === 'R'
}

function mostrarBadgeHallazgoPendiente(criterio: CriterioRespuesta): boolean {
  return (
    mostrarCampoHallazgo(criterio) && criterio.hallazgo_id === null
  )
}

function claseChip(criterio: CriterioRespuesta, valor: string): string {
  if (criterio.respuesta_valor !== valor) return ''
  if (valor === 'V') return 'verde'
  if (valor === 'A') return 'amarillo'
  return 'rojo'
}
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header-info">
        <h1>Ejecutar Auditoría</h1>
        <p class="subtitle">
          Selecciona la auditoría y la célula, responde cada criterio y registra los hallazgos.
        </p>
      </div>
    </header>

    <div v-if="error" class="msg error">{{ error }}</div>
    <div v-if="exito" class="msg success">{{ exito }}</div>

    <!-- Paso 1: Seleccionar auditoría -->
    <div v-if="paso === 'seleccionar'" class="seleccion">
      <div v-if="auditorias.length === 0" class="state state-empty">
        <svg class="state-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M5 3h14v18H5z" stroke="currentColor" stroke-width="1.6" fill="none" stroke-linejoin="round"/>
          <path d="M8 8h8M8 12h8M8 16h5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
        </svg>
        <h2>No hay auditorías disponibles</h2>
        <p>Pide al administrador que active una auditoría para comenzar.</p>
      </div>
      <div v-else class="lista">
        <div
          v-for="auditoria in auditorias"
          :key="auditoria.id"
          class="item"
          @click="seleccionarAuditoria(auditoria)"
        >
          <div class="item-nombre">{{ auditoria.nombre }}</div>
          <div class="item-meta" v-if="auditoria.area_nombre">
            {{ auditoria.area_nombre }} · {{ auditoria.capa_nombre || '' }}
          </div>
        </div>
      </div>
    </div>

    <!-- Paso 2: Seleccionar célula -->
    <div v-if="paso === 'celulas'" class="seleccion">
      <button class="btn" @click="paso = 'seleccionar'">← Volver</button>
      <h2>{{ auditoriaSeleccionada?.nombre }}</h2>
      <div v-if="auditoriaSeleccionada?.area_nombre" class="msg msg-info">
        Área: {{ auditoriaSeleccionada.area_nombre }}
      </div>
      <h3>Selecciona la célula</h3>
      <div v-if="celulas.length === 0" class="state state-empty">
        <h2>No hay células disponibles</h2>
        <p>Esta auditoría no tiene células asignadas en su área.</p>
      </div>
      <div v-else class="lista">
        <div
          v-for="celula in celulas"
          :key="celula.id"
          class="item"
          @click="iniciar(celula)"
        >
          <div class="item-nombre">Célula {{ celula.numero }}</div>
        </div>
      </div>
    </div>

    <!-- Paso 3: Checklist -->
    <div v-if="paso === 'ejecutando' && ejecucion" class="ejecucion">
      <div class="ejecucion-header">
        <div class="ejecucion-head-row">
          <h2>{{ ejecucion.auditoria_nombre }}</h2>
          <span v-if="finalizada" class="estado-final">FINALIZADA</span>
        </div>
        <div class="ejecucion-meta">
          <span v-if="ejecucion.celula_numero">Célula {{ ejecucion.celula_numero }}</span>
          <span v-if="ejecucion.area_nombre">· {{ ejecucion.area_nombre }}</span>
          <span>· {{ ejecucion.auditor_nombre }}</span>
        </div>
        <div class="progreso">
          <div class="progreso-info">
            <span class="progreso-label">Progreso</span>
            <span class="progreso-num" data-num>{{ respondidos }}/{{ total }}</span>
          </div>
          <div class="progreso-barra">
            <div
              class="progreso-relleno"
              :style="{ transform: 'scaleX(' + (total > 0 ? respondidos / total : 0) + ')' }"
            ></div>
          </div>
        </div>
      </div>

      <div class="criterios">
        <div
          v-for="criterio in criterios"
          :key="criterio.id"
          class="criterio"
          :class="{ 'criterio--respondido': criterio.respuesta_valor !== null }"
        >
          <div class="criterio-num">{{ criterio.orden }}</div>
          <div class="criterio-desc">
            <span>{{ criterio.descripcion }}</span>
            <div class="criterio-valores">
              <button
                class="chip-btn verde"
                :class="{ activo: criterio.respuesta_valor === 'V' }"
                :disabled="finalizada"
                @click="seleccionarValor(criterio, 'V')"
              >V</button>
              <button
                class="chip-btn amarillo"
                :class="{ activo: criterio.respuesta_valor === 'A' }"
                :disabled="finalizada"
                @click="seleccionarValor(criterio, 'A')"
              >A</button>
              <button
                class="chip-btn rojo"
                :class="{ activo: criterio.respuesta_valor === 'R' }"
                :disabled="finalizada"
                @click="seleccionarValor(criterio, 'R')"
              >R</button>
              <span
                v-if="mostrarBadgeHallazgoPendiente(criterio)"
                class="badge-pendiente"
                :class="criterio.respuesta_valor === 'A' ? 'badge-amarillo' : 'badge-rojo'"
                title="Aún no has guardado el hallazgo para esta respuesta."
              >Hallazgo pendiente</span>
            </div>
            <div
              v-if="mostrarCampoHallazgo(criterio)"
              class="criterio-hallazgo"
              :class="claseChip(criterio, criterio.respuesta_valor!)"
            >
              <label>
                <strong>
                  {{
                    criterio.respuesta_valor === 'A'
                      ? 'Hallazgo menor (corregido y retroalimentado)'
                      : 'Hallazgo mayor / grave'
                  }}
                </strong>
              </label>
              <textarea
                v-model="hallazgosInputs[criterio.id]"
                class="input hallazgo-input"
                rows="3"
                placeholder="Describe el hallazgo detectado..."
                :disabled="finalizada"
              ></textarea>
              <div class="hallazgo-acciones">
                <button
                  class="btn small"
                  :disabled="finalizada || hallazgosGuardando[criterio.id]"
                  @click="guardarHallazgo(criterio)"
                >
                  {{
                    criterio.hallazgo_id
                      ? 'Actualizar hallazgo'
                      : 'Registrar hallazgo'
                  }}
                </button>
                <button
                  v-if="criterio.hallazgo_id && !finalizada"
                  class="btn small danger"
                  @click="quitarHallazgo(criterio)"
                >
                  Quitar hallazgo
                </button>
              </div>
              <div v-if="hallazgosError[criterio.id]" class="msg error small">
                {{ hallazgosError[criterio.id] }}
              </div>
              <div v-else-if="criterio.hallazgo_id" class="msg success small">
                Hallazgo #{{ criterio.hallazgo_id }} registrado.
              </div>
            </div>
          </div>
          <div
            v-if="criterio.respuesta_valor && criterio.respuesta_valor !== 'V' && !mostrarCampoHallazgo(criterio)"
            class="criterio-obs"
          >
            <input
              v-model="criterio.respuesta_observaciones"
              class="input"
              placeholder="Observaciones..."
              type="text"
              :disabled="finalizada"
            />
          </div>
        </div>
      </div>

      <div class="acciones">
        <button
          class="btn"
          :disabled="cargando || finalizada"
          @click="guardar"
        >Guardar</button>
        <button
          class="btn primary"
          :disabled="cargando || respondidos < total || finalizada"
          @click="finalizar"
        >Finalizar Auditoría</button>
      </div>
    </div>

    <!-- Paso 4: Terminado -->
    <div v-if="paso === 'terminado' && ejecucion" class="terminado">
      <span class="terminado-icon">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 4h16v16H4z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" fill="none"/>
          <path d="M8 12.2l2.8 2.8L16.5 9" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
        </svg>
      </span>
      <h2>Auditoría finalizada</h2>
      <p class="terminado-sub">La ejecución quedó registrada en el historial.</p>
      <div class="resumen">
        <p><strong>{{ ejecucion.auditoria_nombre }}</strong></p>
        <p v-if="ejecucion.celula_numero">Célula {{ ejecucion.celula_numero }} · {{ ejecucion.area_nombre }}</p>
        <p>Fecha: {{ new Date(ejecucion.fecha).toLocaleString() }}</p>
        <p class="resumen-total" data-num>{{ respondidos }}/{{ total }} criterios respondidos</p>
      </div>
      <button class="btn primary" @click="router.push({ name: 'dashboard' })">
        Volver al inicio
      </button>
    </div>
  </div>
</template>

<style scoped>
/* --- Selección de auditoría / célula --- */
.seleccion h2 {
  margin: 1rem 0 0.25rem;
  font-size: var(--text-lg, 1.0625rem);
}

.seleccion h3 {
  margin: 1.4rem 0 0.75rem;
  font-size: var(--text-md, 0.9375rem);
  color: var(--c-ink-2, #334155);
}

.lista {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.item {
  padding: 1rem 1.15rem;
  border: 1px solid var(--c-line, #e6e9ef);
  border-radius: var(--r-md, 10px);
  background: var(--c-surface, #fff);
  cursor: pointer;
  box-shadow: var(--sh-sm, 0 1px 2px rgba(15, 23, 42, 0.05));
  transition: border-color 0.15s var(--ease), box-shadow 0.15s var(--ease);
}

.item:hover {
  border-color: var(--c-primary, #2563eb);
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.12);
}

.item-nombre {
  font-weight: 600;
  color: var(--c-ink, #0f172a);
}

.item-meta {
  color: var(--c-ink-3, #64748b);
  font-size: 0.82rem;
  margin-top: 0.25rem;
}

/* --- Encabezado de ejecución --- */
.ejecucion-header {
  background: var(--c-surface-2, #f8fafc);
  border: 1px solid var(--c-line, #e6e9ef);
  border-radius: var(--r-lg, 14px);
  padding: 1rem 1.25rem;
  margin-bottom: 1.25rem;
}

.ejecucion-head-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.ejecucion-header h2 {
  font-size: var(--text-lg, 1.0625rem);
}

.estado-final {
  color: var(--c-danger, #dc2626);
  font-weight: 800;
  font-size: 0.75rem;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.ejecucion-meta {
  color: var(--c-ink-3, #64748b);
  font-size: 0.84rem;
  margin-top: 0.3rem;
}

.progreso {
  margin-top: 0.9rem;
}

.progreso-info {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 0.4rem;
}

.progreso-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--c-ink-3, #64748b);
}

.progreso-num {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--c-ink-2, #334155);
}

.progreso-barra {
  height: 8px;
  background: var(--c-line, #e6e9ef);
  border-radius: 999px;
  overflow: hidden;
}

.progreso-relleno {
  height: 100%;
  background: var(--c-primary, #2563eb);
  border-radius: 999px;
  transform-origin: left;
  transition: transform 0.3s var(--ease);
}

/* --- Checklist --- */
.criterios {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.criterio {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.85rem 1rem;
  border: 1px solid var(--c-line, #e6e9ef);
  border-radius: var(--r-md, 10px);
  background: var(--c-surface, #fff);
  transition: border-color 0.15s var(--ease), box-shadow 0.15s var(--ease);
}

.criterio--respondido {
  border-color: var(--c-line-3, #cbd5e1);
}

.criterio-num {
  min-width: 1.85rem;
  height: 1.85rem;
  border-radius: 50%;
  background: var(--c-surface-3, #f1f5f9);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--c-ink-3, #64748b);
  flex-shrink: 0;
}

.criterio-desc {
  flex: 1;
  min-width: 0;
}

.criterio-desc > span {
  display: block;
  font-size: 0.9rem;
  color: var(--c-ink-2, #334155);
  line-height: 1.45;
  margin-bottom: 0.55rem;
}

.criterio-valores {
  display: flex;
  gap: 0.35rem;
  align-items: center;
  flex-wrap: wrap;
}

.chip-btn {
  min-width: 2rem;
  padding: 0.3rem 0.7rem;
  border: 1.5px solid var(--c-line-3, #cbd5e1);
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
  background: var(--c-surface, #fff);
  color: var(--c-ink-3, #64748b);
  transition: border-color 0.12s var(--ease), background 0.12s var(--ease), color 0.12s var(--ease);
  font-family: inherit;
}

.chip-btn:hover {
  border-color: var(--c-ink-4, #94a3b8);
}

.chip-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.chip-btn.verde {
  color: var(--c-ok, #16a34a);
  border-color: var(--c-ok, #16a34a);
}

.chip-btn.verde.activo {
  background: var(--c-ok, #16a34a);
  color: #fff;
}

.chip-btn.amarillo {
  color: var(--c-warn, #d97706);
  border-color: var(--c-warn, #d97706);
}

.chip-btn.amarillo.activo {
  background: var(--c-warn, #d97706);
  color: #fff;
}

.chip-btn.rojo {
  color: var(--c-danger, #dc2626);
  border-color: var(--c-danger, #dc2626);
}

.chip-btn.rojo.activo {
  background: var(--c-danger, #dc2626);
  color: #fff;
}

.badge-pendiente {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.18rem 0.6rem;
  border-radius: 999px;
  margin-left: 0.35rem;
  white-space: nowrap;
}

.badge-pendiente.badge-amarillo {
  background: var(--c-warn-soft, #fef3c7);
  color: var(--c-warn-ink, #92400e);
}

.badge-pendiente.badge-rojo {
  background: var(--c-danger-soft, #fee2e2);
  color: var(--c-danger-ink, #b91c1c);
}

.criterio-obs {
  width: 100%;
  margin-top: 0.55rem;
}

.criterio-obs .input {
  width: 100%;
  box-sizing: border-box;
}

.criterio-hallazgo {
  margin-top: 0.75rem;
  padding: 0.8rem;
  border-radius: var(--r-md, 10px);
  border: 1px solid var(--c-line, #e6e9ef);
  background: var(--c-surface-2, #f8fafc);
}

.criterio-hallazgo.amarillo {
  border-color: #fcd34d;
  background: var(--c-warn-soft, #fef3c7);
}

.criterio-hallazgo.rojo {
  border-color: #fca5a5;
  background: var(--c-danger-soft, #fee2e2);
}

.criterio-hallazgo label {
  display: block;
  margin-bottom: 0.4rem;
  font-size: 0.85rem;
}

.criterio-hallazgo label strong {
  color: var(--c-ink, #0f172a);
}

.hallazgo-input {
  width: 100%;
  box-sizing: border-box;
  resize: vertical;
}

.hallazgo-acciones {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.6rem;
  flex-wrap: wrap;
}

/* --- Acciones finales --- */
.acciones {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

/* --- Terminado --- */
.terminado {
  text-align: center;
  padding: 2rem 1rem;
}

.terminado-icon {
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 1rem;
  background: var(--c-ok-soft, #dcfce7);
  color: var(--c-ok, #16a34a);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.terminado-icon svg {
  width: 1.9rem;
  height: 1.9rem;
}

.terminado h2 {
  font-size: var(--text-xl, 1.375rem);
}

.terminado-sub {
  color: var(--c-ink-3, #64748b);
  font-size: 0.9rem;
  margin-top: 0.35rem;
}

.resumen {
  margin: 1.5rem auto;
  max-width: 360px;
  background: var(--c-surface-2, #f8fafc);
  border: 1px solid var(--c-line, #e6e9ef);
  border-radius: var(--r-lg, 14px);
  padding: 1rem 1.25rem;
}

.resumen p {
  margin: 0.25rem 0;
  color: var(--c-ink-3, #64748b);
  font-size: 0.9rem;
}

.resumen-total {
  font-weight: 700;
  color: var(--c-ink, #0f172a);
}
</style>
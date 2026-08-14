<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
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

const router = useRouter()
const authStore = useAuthStore()

const paso = ref<'seleccionar' | 'celulas' | 'ejecutando' | 'terminado'>('seleccionar')
const error = ref('')
const exito = ref('')
const cargando = ref(false)

const auditorias = ref<Auditoria[]>([])
const auditoriaSeleccionada = ref<Auditoria | null>(null)
const celulas = ref<Celula[]>([])
const ejecucion = ref<EjecucionAuditoria | null>(null)

const criterios = computed(() => ejecucion.value?.criterios || [])
const respondidos = computed(() =>
  criterios.value.filter((c) => c.respuesta_valor !== null).length,
)
const total = computed(() => criterios.value.length)

async function mostrarError(prefix: string, err: unknown) {
  const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || String(err)
  error.value = `${prefix}: ${msg}`
}

function limpiarMensajes() {
  error.value = ''
  exito.value = ''
}

onMounted(async () => {
  try {
    auditorias.value = await obtenerAuditoriasDisponibles()
  } catch (err) {
    mostrarError('Error al cargar auditorías', err)
  }
})

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
    paso.value = 'ejecutando'
  } catch (err) {
    mostrarError('Error al iniciar ejecución', err)
  } finally {
    cargando.value = false
  }
}

function seleccionarValor(criterio: CriterioRespuesta, valor: string) {
  criterio.respuesta_valor = criterio.respuesta_valor === valor ? null : valor
  if (valor === 'V') {
    criterio.respuesta_observaciones = null
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

const valorLabel: Record<string, string> = { V: 'V', A: 'A', R: 'R' }
const valorColor: Record<string, string> = { V: 'verde', A: 'amarillo', R: 'rojo' }
</script>

<template>
  <div class="page">
    <h1>Ejecutar Auditoría</h1>

    <div v-if="error" class="msg error">{{ error }}</div>
    <div v-if="exito" class="msg success">{{ exito }}</div>

    <!-- Paso 1: Seleccionar auditoría -->
    <div v-if="paso === 'seleccionar'" class="seleccion">
      <h2>Selecciona una auditoría</h2>
      <div v-if="auditorias.length === 0" class="msg">No hay auditorías disponibles.</div>
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
      <div v-if="auditoriaSeleccionada?.area_nombre" class="msg">
        Área: {{ auditoriaSeleccionada.area_nombre }}
      </div>
      <h3>Selecciona la célula</h3>
      <div v-if="celulas.length === 0" class="msg">
        No hay células disponibles en esta área.
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
        <h2>{{ ejecucion.auditoria_nombre }}</h2>
        <div class="ejecucion-meta">
          <span v-if="ejecucion.celula_numero">Célula {{ ejecucion.celula_numero }}</span>
          <span v-if="ejecucion.area_nombre">· {{ ejecucion.area_nombre }}</span>
          <span>· {{ ejecucion.auditor_nombre }}</span>
        </div>
        <div class="progreso">
          <div class="progreso-barra">
            <div
              class="progreso-relleno"
              :style="{ width: total > 0 ? (respondidos / total) * 100 + '%' : '0%' }"
            ></div>
          </div>
          <span>{{ respondidos }}/{{ total }} respondidos</span>
        </div>
      </div>

      <div class="criterios">
        <div
          v-for="criterio in criterios"
          :key="criterio.id"
          class="criterio"
        >
          <div class="criterio-num">{{ criterio.orden }}</div>
          <div class="criterio-desc">
            <span>{{ criterio.descripcion }}</span>
            <div class="criterio-valores">
              <button
                class="chip-btn verde"
                :class="{ activo: criterio.respuesta_valor === 'V' }"
                @click="seleccionarValor(criterio, 'V')"
              >V</button>
              <button
                class="chip-btn amarillo"
                :class="{ activo: criterio.respuesta_valor === 'A' }"
                @click="seleccionarValor(criterio, 'A')"
              >A</button>
              <button
                class="chip-btn rojo"
                :class="{ activo: criterio.respuesta_valor === 'R' }"
                @click="seleccionarValor(criterio, 'R')"
              >R</button>
            </div>
          </div>
          <div
            v-if="criterio.respuesta_valor && criterio.respuesta_valor !== 'V'"
            class="criterio-obs"
          >
            <input
              v-model="criterio.respuesta_observaciones"
              class="input"
              placeholder="Observaciones..."
              type="text"
            />
          </div>
        </div>
      </div>

      <div class="acciones">
        <button
          class="btn"
          :disabled="cargando"
          @click="guardar"
        >Guardar</button>
        <button
          class="btn primary"
          :disabled="cargando || respondidos < total"
          @click="finalizar"
        >Finalizar Auditoría</button>
      </div>
    </div>

    <!-- Paso 4: Terminado -->
    <div v-if="paso === 'terminado' && ejecucion" class="terminado">
      <h2>Auditoría finalizada</h2>
      <div class="resumen">
        <p><strong>{{ ejecucion.auditoria_nombre }}</strong></p>
        <p v-if="ejecucion.celula_numero">Célula {{ ejecucion.celula_numero }} · {{ ejecucion.area_nombre }}</p>
        <p>Fecha: {{ new Date(ejecucion.fecha).toLocaleString() }}</p>
        <p>{{ respondidos }}/{{ total }} criterios respondidos</p>
      </div>
      <button class="btn primary" @click="router.push({ name: 'dashboard' })">
        Volver al inicio
      </button>
    </div>
  </div>
</template>

<style scoped>
.page { max-width: 900px; margin: 0 auto; padding: 2rem; }
h1 { margin-bottom: 1.5rem; }

.msg { padding: .75rem 1rem; border-radius: 6px; margin-bottom: 1rem; background: #f0f0f0; }
.msg.error { background: #fee; color: #c00; border: 1px solid #fcc; }
.msg.success { background: #efe; color: #060; border: 1px solid #cfc; }

.seleccion h2 { margin-bottom: .25rem; }
.seleccion h3 { margin: 1.5rem 0 .75rem; }

.lista { display: flex; flex-direction: column; gap: .5rem; }
.item {
  padding: 1rem; border: 1px solid #ddd; border-radius: 8px; cursor: pointer;
  transition: background .15s, border-color .15s;
}
.item:hover { background: #f5f7ff; border-color: #88a; }
.item-nombre { font-weight: 600; }
.item-meta { color: #666; font-size: .875rem; margin-top: .25rem; }

.ejecucion-header {
  background: #f9f9fb; border: 1px solid #e0e0e8; border-radius: 8px;
  padding: 1rem 1.25rem; margin-bottom: 1.5rem;
}
.ejecucion-header h2 { margin: 0 0 .25rem; }
.ejecucion-meta { color: #666; font-size: .875rem; margin-bottom: .75rem; }
.progreso { display: flex; align-items: center; gap: .75rem; font-size: .875rem; color: #444; }
.progreso-barra { flex: 1; height: 8px; background: #e0e0e8; border-radius: 4px; overflow: hidden; }
.progreso-relleno { height: 100%; background: #4c6; border-radius: 4px; transition: width .3s; }

.criterios { display: flex; flex-direction: column; gap: .5rem; margin-bottom: 1.5rem; }
.criterio {
  display: flex; align-items: flex-start; gap: .75rem;
  padding: .75rem 1rem; border: 1px solid #e8e8ec; border-radius: 8px;
}
.criterio-num {
  min-width: 28px; height: 28px; border-radius: 50%;
  background: #e8e8ec; display: flex; align-items: center; justify-content: center;
  font-size: .75rem; font-weight: 700; color: #555;
}
.criterio-desc { flex: 1; }
.criterio-desc span { display: block; margin-bottom: .5rem; }
.criterio-valores { display: flex; gap: .25rem; }
.criterio-obs { width: 100%; margin-top: .5rem; }
.criterio-obs .input { width: 100%; }

.input {
  padding: .5rem .75rem; border: 1px solid #ccc; border-radius: 6px; font-size: .875rem;
  outline: none; box-sizing: border-box;
}
.input:focus { border-color: #88a; }

.chip-btn {
  padding: .25rem .65rem; border: 1px solid #ccc; border-radius: 16px;
  font-size: .75rem; font-weight: 700; cursor: pointer; background: #fff;
  transition: all .15s;
}
.chip-btn:hover { opacity: .85; }
.chip-btn.activo { transform: scale(1.1); }

.chip-btn.verde { color: #2a2; border-color: #2a2; }
.chip-btn.verde.activo { background: #2a2; color: #fff; }

.chip-btn.amarillo { color: #b80; border-color: #b80; }
.chip-btn.amarillo.activo { background: #b80; color: #fff; }

.chip-btn.rojo { color: #c22; border-color: #c22; }
.chip-btn.rojo.activo { background: #c22; color: #fff; }

.acciones { display: flex; gap: .75rem; justify-content: flex-end; }
.btn {
  padding: .5rem 1.25rem; border: 1px solid #ccc; border-radius: 6px;
  background: #fff; cursor: pointer; font-size: .875rem;
}
.btn:disabled { opacity: .5; cursor: not-allowed; }
.btn.primary { background: #36c; color: #fff; border-color: #36c; }
.btn.primary:disabled { background: #88a; border-color: #88a; }

.terminado { text-align: center; }
.resumen { margin: 1rem 0 1.5rem; }
.resumen p { margin: .25rem 0; color: #555; }
</style>

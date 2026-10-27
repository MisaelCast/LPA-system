<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Auditoria } from '@/types/auditoria'
import type { Celula } from '@/types/area'
import type { EjecucionAuditoria, CriterioRespuesta } from '@/types/ejecucion'
import PlanSemanal from '@/components/PlanSemanal.vue'
import {
  obtenerAuditoriasDisponibles,
  obtenerCelulasDisponibles,
  iniciarEjecucion,
  obtenerEjecucion,
  guardarRespuestas,
  finalizarEjecucion,
  iniciarPendiente,
} from '@/services/ejecucion.service'
import {
  crearHallazgo,
  actualizarHallazgo,
  eliminarHallazgo,
  subirEvidencia,
  listarEvidencias,
  eliminarEvidencia,
  responsablesDeArea,
} from '@/services/hallazgo.service'
import type { Evidencia, ResponsableResumen } from '@/types/hallazgo'

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
const responsables = ref<ResponsableResumen[]>([])
const responsableId = ref<number | null>(null)
const responsablesCargando = ref(false)
const responsablesError = ref('')

const hallazgosInputs = ref<Record<number, string>>({})
const hallazgosGuardando = ref<Record<number, boolean>>({})
const hallazgosError = ref<Record<number, string>>({})
const hallazgosFotos = ref<Record<number, Evidencia[]>>({})
const fotosPendientes = ref<Record<number, { file: File; preview: string }[]>>({})
const fotosSubiendo = ref<Record<number, boolean>>({})
const inputFotos = ref<HTMLInputElement | null>(null)
const criterioFotosActivo = ref<CriterioRespuesta | null>(null)

const criterios = computed(() => ejecucion.value?.criterios || [])
const tituloAuditoria = computed(() =>
  (ejecucion.value?.auditoria_nombre ?? '').replace(' - ', '\u00a0- '),
)
const respondidos = computed(() =>
  criterios.value.filter((c) => c.respuesta_valor !== null).length,
)
const total = computed(() => criterios.value.length)
const finalizada = computed(() => ejecucion.value?.estado === 'finalizada')
const esPendiente = computed(() => ejecucion.value?.estado === 'pendiente')
const noElaborada = computed(() => ejecucion.value?.estado === 'no_elaborada')
const soloLectura = computed(() => finalizada.value || noElaborada.value)
const bloqueado = computed(() => soloLectura.value || esPendiente.value)

async function iniciarPendienteLocal() {
  if (!ejecucion.value) return
  limpiarMensajes()
  cargando.value = true
  try {
    ejecucion.value = await iniciarPendiente(ejecucion.value.id)
    sincronizarBorradorHallazgos()
  } catch (err) {
    mostrarError('Error al iniciar la ejecución programada', err)
  } finally {
    cargando.value = false
  }
}

function esCumplimiento(): boolean {
  return ejecucion.value?.tipo_respuesta === 'cumplimiento'
}

const opcionesRespuesta = computed(() =>
  esCumplimiento()
    ? [
        { valor: 'cumple', label: 'Cumple', css: 'verde' },
        { valor: 'no_cumple', label: 'No cumple', css: 'rojo' },
        { valor: 'na', label: 'N/A', css: 'neutro' },
      ]
    : [
        { valor: 'V', label: 'V', css: 'verde' },
        { valor: 'A', label: 'A', css: 'amarillo' },
        { valor: 'R', label: 'R', css: 'rojo' },
      ],
)

type FilaHeader = {
  tipo: 'header'
  nivel: 'seccion' | 'subseccion' | 'subtitulo'
  texto: string
}
type FilaCriterio = { tipo: 'criterio'; criterio: CriterioRespuesta }
type Fila = FilaHeader | FilaCriterio

const filas = computed<Fila[]>(() => {
  const resultado: Fila[] = []
  let seccion = ''
  let subseccion = ''
  let subtitulo = ''
  for (const c of criterios.value) {
    if (c.seccion && c.seccion !== seccion) {
      seccion = c.seccion
      subseccion = ''
      subtitulo = ''
      resultado.push({ tipo: 'header', nivel: 'seccion', texto: seccion })
    }
    if (c.subseccion && c.subseccion !== subseccion) {
      subseccion = c.subseccion
      subtitulo = ''
      resultado.push({ tipo: 'header', nivel: 'subseccion', texto: subseccion })
    }
    if (c.subtitulo && c.subtitulo !== subtitulo) {
      subtitulo = c.subtitulo
      resultado.push({ tipo: 'header', nivel: 'subtitulo', texto: subtitulo })
    }
    resultado.push({ tipo: 'criterio', criterio: c })
  }
  return resultado
})

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

async function cargarResponsables(areaId: number | null): Promise<void> {
  responsablesError.value = ''
  if (!areaId) {
    responsables.value = []
    responsableId.value = null
    responsablesCargando.value = false
    return
  }
  responsablesCargando.value = true
  try {
    const lista = await responsablesDeArea(areaId)
    responsables.value = lista
    responsableId.value =
      lista.length === 1 ? (lista[0]?.id ?? null) : null
  } catch {
    responsables.value = []
    responsableId.value = null
    responsablesError.value = 'No se pudieron cargar los responsables del área.'
  } finally {
    responsablesCargando.value = false
  }
}

watch(
  () => ejecucion.value?.area_id ?? null,
  (areaId) => {
    void cargarResponsables(areaId)
  },
)

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
  if (!auditoria.requiere_celula) {
    iniciar(null)
    return
  }
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

async function iniciar(celula: Celula | null) {
  limpiarMensajes()
  cargando.value = true
  try {
    const ej = await iniciarEjecucion(auditoriaSeleccionada.value!.id, {
      celula_id: celula ? celula.id : null,
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
  void cargarFotosExistentes()
}

async function cargarFotosExistentes() {
  if (!ejecucion.value) return
  const conHallazgo = criterios.value.filter((c) => c.hallazgo_id !== null)
  await Promise.all(
    conHallazgo.map(async (c) => {
      try {
        hallazgosFotos.value[c.id] = await listarEvidencias(c.hallazgo_id!)
      } catch {
        /* sin fotos o sin permiso: se omite en silencio */
      }
    }),
  )
}

function abrirSelectorFotos(criterio: CriterioRespuesta) {
  criterioFotosActivo.value = criterio
  inputFotos.value?.click()
}

function onFotosSeleccionadas(event: Event) {
  const input = event.target as HTMLInputElement
  const criterio = criterioFotosActivo.value
  if (!criterio || !input.files?.length) return
  const nuevos: { file: File; preview: string }[] = []
  for (const file of Array.from(input.files)) {
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      hallazgosError.value[criterio.id] =
        'Formato no permitido. Usa archivos JPG, PNG o WEBP.'
      continue
    }
    if (file.size > 5 * 1024 * 1024) {
      hallazgosError.value[criterio.id] = 'La imagen supera el límite de 5 MB.'
      continue
    }
    nuevos.push({ file, preview: URL.createObjectURL(file) })
  }
  if (nuevos.length) {
    fotosPendientes.value[criterio.id] = [
      ...(fotosPendientes.value[criterio.id] ?? []),
      ...nuevos,
    ]
  }
  input.value = ''
}

function quitarFotoPendiente(criterioId: number, indice: number) {
  const lista = fotosPendientes.value[criterioId] ?? []
  const pendiente = lista[indice]
  if (pendiente) {
    URL.revokeObjectURL(pendiente.preview)
  }
  fotosPendientes.value[criterioId] = lista.filter((_, i) => i !== indice)
}

async function subirFotosPendientes(criterioId: number, hallazgoId: number) {
  const pendientes = fotosPendientes.value[criterioId] ?? []
  if (!pendientes.length) return
  fotosSubiendo.value[criterioId] = true
  try {
    for (const pendiente of pendientes) {
      const evidencia = await subirEvidencia(hallazgoId, pendiente.file)
      URL.revokeObjectURL(pendiente.preview)
      hallazgosFotos.value[criterioId] = [
        ...(hallazgosFotos.value[criterioId] ?? []),
        evidencia,
      ]
    }
    fotosPendientes.value[criterioId] = []
  } finally {
    fotosSubiendo.value[criterioId] = false
  }
}

async function eliminarFoto(criterioId: number, evidenciaId: number) {
  try {
    await eliminarEvidencia(evidenciaId)
    hallazgosFotos.value[criterioId] = (
      hallazgosFotos.value[criterioId] ?? []
    ).filter((e) => e.id !== evidenciaId)
  } catch (err) {
    mostrarError('No se pudo eliminar la foto', err)
  }
}

function limpiarFotos(criterioId: number) {
  for (const pendiente of fotosPendientes.value[criterioId] ?? []) {
    URL.revokeObjectURL(pendiente.preview)
  }
  delete fotosPendientes.value[criterioId]
  hallazgosFotos.value[criterioId] = []
  delete fotosSubiendo.value[criterioId]
}

async function seleccionarValor(criterio: CriterioRespuesta, valor: string) {
  if (soloLectura.value) return
  criterio.respuesta_valor = criterio.respuesta_valor === valor ? null : valor
  if (valorEsNoHallazgo(criterio.respuesta_valor)) {
    criterio.respuesta_observaciones = null
    if (criterio.hallazgo_id !== null && !soloLectura.value) {
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
    limpiarFotos(criterio.id)
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
  if (soloLectura.value) {
    hallazgosError.value[criterio.id] =
      'La ejecución está cerrada, no se pueden modificar hallazgos.'
    return
  }
  const descripcion = (hallazgosInputs.value[criterio.id] ?? '').trim()
  if (!descripcion) {
    hallazgosError.value[criterio.id] = 'La descripción es obligatoria.'
    return
  }
  if (
    criterio.hallazgo_id === null &&
    !esCumplimiento() &&
    responsables.value.length > 0 &&
    responsableId.value === null
  ) {
    hallazgosError.value[criterio.id] =
      'Selecciona el responsable que atenderá el hallazgo.'
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
        area_responsable_id: ejecucion.value?.area_id ?? null,
        responsable_id: responsableId.value,
      })
      crit.hallazgo_id = creado.id
      crit.hallazgo_descripcion = creado.descripcion
      hallazgosInputs.value[crit.id] = creado.descripcion
    }
    try {
      await subirFotosPendientes(crit.id, crit.hallazgo_id!)
    } catch {
      hallazgosError.value[crit.id] =
        'El hallazgo se guardó, pero no se pudieron subir las fotos. Intenta de nuevo.'
      return
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
      if (mostrarCampoHallazgo(c)) {
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

function valorEsNoHallazgo(valor: string | null): boolean {
  if (esCumplimiento()) return valor === 'cumple' || valor === 'na'
  return valor === 'V'
}

function mostrarCampoHallazgo(criterio: CriterioRespuesta): boolean {
  if (esCumplimiento()) return criterio.respuesta_valor === 'no_cumple'
  return criterio.respuesta_valor === 'A' || criterio.respuesta_valor === 'R'
}

function etiquetaHallazgo(valor: string | null): string {
  if (esCumplimiento()) return 'Hallazgo de verificación (no cumple)'
  return valor === 'A'
    ? 'Hallazgo menor (corregido y retroalimentado)'
    : 'Hallazgo mayor / grave'
}

function tieneFotos(criterioId: number): boolean {
  return (
    (hallazgosFotos.value[criterioId]?.length ?? 0) > 0 ||
    (fotosPendientes.value[criterioId]?.length ?? 0) > 0
  )
}

function mostrarBadgeHallazgoPendiente(criterio: CriterioRespuesta): boolean {
  return (
    mostrarCampoHallazgo(criterio) && criterio.hallazgo_id === null
  )
}

function claseChip(criterio: CriterioRespuesta, valor: string): string {
  if (criterio.respuesta_valor !== valor) return ''
  if (valor === 'V' || valor === 'cumple') return 'verde'
  if (valor === 'A') return 'amarillo'
  if (valor === 'na') return 'neutro'
  return 'rojo'
}
</script>

<template>
  <div class="page">
    <div v-if="error" class="msg error">{{ error }}</div>
    <div v-if="exito" class="msg success">{{ exito }}</div>

    <input
      ref="inputFotos"
      type="file"
      accept="image/jpeg,image/png,image/webp"
      multiple
      hidden
      @change="onFotosSeleccionadas"
    />

    <!-- Paso 1: Seleccionar auditoría -->
    <div v-if="paso === 'seleccionar'" class="seleccion">
      <PlanSemanal />

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
      <header
        class="audit-docket"
        :class="{ 'audit-docket--sticky': !esPendiente }"
      >
        <div class="docket-main">
          <div class="docket-id">
            <div class="docket-title-row">
              <h2 class="docket-title">{{ tituloAuditoria }}</h2>
              <span
                v-if="finalizada"
                class="docket-status docket-status--final"
              >
                <span class="status-dot" aria-hidden="true"></span>Finalizada
              </span>
              <span
                v-else-if="noElaborada"
                class="docket-status docket-status--muted"
              >
                <span class="status-dot" aria-hidden="true"></span>No elaborada
              </span>
              <span
                v-else-if="esPendiente"
                class="docket-status docket-status--pending"
              >
                <span class="status-dot" aria-hidden="true"></span>Pendiente
              </span>
            </div>
            <div class="docket-meta">
              <span v-if="ejecucion.celula_numero" class="docket-meta-item">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <rect x="3.5" y="3.5" width="17" height="17" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.6"/>
                  <path d="M3.5 9h17M9 3.5v17" fill="none" stroke="currentColor" stroke-width="1.6"/>
                </svg>
                Célula {{ ejecucion.celula_numero }}
              </span>
              <span v-if="ejecucion.area_nombre" class="docket-meta-item">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M4 20.5V9.5l5 3v-3l5 3v-4l6 4v8z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
                  <path d="M4 20.5h16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                </svg>
                {{ ejecucion.area_nombre }}
              </span>
              <span class="docket-meta-item">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="12" cy="8.2" r="3.3" fill="none" stroke="currentColor" stroke-width="1.6"/>
                  <path d="M5.4 20c0-3.5 2.9-5.9 6.6-5.9s6.6 2.4 6.6 5.9" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                </svg>
                {{ ejecucion.auditor_nombre }}
              </span>
            </div>
          </div>

          <div v-if="!esPendiente" class="docket-progress">
            <div class="docket-progress-head">
              <span class="docket-progress-label">Progreso</span>
              <span class="docket-progress-value" data-num>
                <strong>{{ respondidos }}</strong><span>/{{ total }}</span>
              </span>
            </div>
            <div
              class="docket-track"
              role="progressbar"
              :aria-valuenow="respondidos"
              aria-valuemin="0"
              :aria-valuemax="total"
              :aria-label="`${respondidos} de ${total} criterios respondidos`"
            >
              <span
                v-for="criterio in criterios"
                :key="'seg-' + criterio.id"
                class="docket-seg"
                :class="{ 'is-done': criterio.respuesta_valor !== null }"
                :title="`Criterio ${criterio.orden}: ${criterio.respuesta_valor !== null ? 'respondido' : 'pendiente'}`"
              ></span>
            </div>
          </div>
        </div>

        <div v-if="esPendiente" class="pendiente-aviso">
          <p>
            Esta es una auditoría programada. Iníciala para responder los criterios.
          </p>
          <button
            class="btn primary"
            :disabled="cargando"
            @click="iniciarPendienteLocal"
          >
            {{ cargando ? 'Iniciando…' : 'Iniciar auditoría' }}
          </button>
        </div>
      </header>

      <div class="criterios">
        <template
          v-for="fila in filas"
          :key="fila.tipo === 'criterio' ? 'c-' + fila.criterio.id : 'h-' + fila.nivel + '-' + fila.texto"
        >
          <div
            v-if="fila.tipo === 'header'"
            class="criterio-head"
            :class="'criterio-head--' + fila.nivel"
          >
            {{ fila.texto }}
          </div>
          <div
            v-else
            class="criterio"
            :class="{ 'criterio--respondido': fila.criterio.respuesta_valor !== null }"
          >
            <div class="criterio-num">{{ fila.criterio.orden }}</div>
            <div class="criterio-desc">
              <span>{{ fila.criterio.descripcion }}</span>
              <div class="criterio-valores">
                <button
                  v-for="op in opcionesRespuesta"
                  :key="op.valor"
                  class="chip-btn"
                  :class="[op.css, { activo: fila.criterio.respuesta_valor === op.valor }]"
                  :disabled="bloqueado"
                  @click="seleccionarValor(fila.criterio, op.valor)"
                >{{ op.label }}</button>
                <span
                  v-if="mostrarBadgeHallazgoPendiente(fila.criterio)"
                  class="badge-pendiente"
                  :class="fila.criterio.respuesta_valor === 'A' ? 'badge-amarillo' : 'badge-rojo'"
                  title="Aún no has guardado el hallazgo para esta respuesta."
                >Hallazgo pendiente</span>
              </div>
              <div
                v-if="mostrarCampoHallazgo(fila.criterio)"
                class="criterio-hallazgo"
                :class="claseChip(fila.criterio, fila.criterio.respuesta_valor!)"
              >
                <label>
                  <strong>{{ etiquetaHallazgo(fila.criterio.respuesta_valor) }}</strong>
                </label>
                <div
                  v-if="fila.criterio.hallazgo_id === null && !esCumplimiento()"
                  class="hallazgo-area"
                >
                  <span>Responsable</span>
                  <p v-if="responsablesCargando" class="hallazgo-aviso">
                    Buscando responsables del área…
                  </p>
                  <p v-else-if="responsablesError" class="hallazgo-aviso err">
                    {{ responsablesError }}
                  </p>
                  <p v-else-if="responsables.length === 0" class="hallazgo-aviso">
                    Esta área no tiene responsables de manufactura asignados.
                  </p>
                  <div v-else-if="responsables.length === 1" class="hallazgo-responsable">
                    <strong>{{ responsables[0]?.nombre }}</strong>
                    <small>{{ responsables[0]?.correo }}</small>
                  </div>
                  <select
                    v-else
                    v-model.number="responsableId"
                    class="input"
                    :disabled="soloLectura"
                  >
                    <option :value="null" disabled>Seleccione el responsable</option>
                    <option v-for="r in responsables" :key="r.id" :value="r.id">
                      {{ r.nombre }}
                    </option>
                  </select>
                </div>
                <textarea
                  v-model="hallazgosInputs[fila.criterio.id]"
                  class="input hallazgo-input"
                  rows="3"
                  placeholder="Describe el hallazgo detectado..."
                  :disabled="soloLectura"
                ></textarea>
                <div class="hallazgo-fotos">
                  <button
                    type="button"
                    class="foto-add"
                    :disabled="soloLectura || fotosSubiendo[fila.criterio.id]"
                    @click="abrirSelectorFotos(fila.criterio)"
                  >
                    <span class="foto-add-icon" aria-hidden="true">
                      <svg viewBox="0 0 24 24">
                        <path d="M4 8.5h3.2l1.4-2h6.8l1.4 2H20v9.5H4z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
                        <circle cx="12" cy="13.2" r="3.1" fill="none" stroke="currentColor" stroke-width="1.6"/>
                      </svg>
                    </span>
                    <span class="foto-add-text">
                      <strong>
                        {{
                          fotosSubiendo[fila.criterio.id]
                            ? 'Subiendo…'
                            : tieneFotos(fila.criterio.id)
                              ? 'Agregar otra foto'
                              : 'Agregar foto'
                        }}
                      </strong>
                      <small>JPG, PNG o WEBP · máx. 5 MB</small>
                    </span>
                  </button>
                  <div
                    v-if="tieneFotos(fila.criterio.id)"
                    class="fotos-grid"
                  >
                    <div
                      v-for="foto in hallazgosFotos[fila.criterio.id]"
                      :key="'ev-' + foto.id"
                      class="foto-thumb"
                    >
                      <a :href="foto.url ?? undefined" target="_blank" rel="noopener">
                        <img :src="foto.url ?? undefined" alt="Evidencia" />
                      </a>
                      <button
                        v-if="!soloLectura"
                        type="button"
                        class="foto-quitar"
                        title="Eliminar foto"
                        @click="eliminarFoto(fila.criterio.id, foto.id)"
                      >
                        ×
                      </button>
                    </div>
                    <div
                      v-for="(pendiente, idx) in fotosPendientes[fila.criterio.id]"
                      :key="'pend-' + idx"
                      class="foto-thumb pendiente"
                    >
                      <img :src="pendiente.preview" alt="Foto pendiente" />
                      <span class="foto-etiqueta">pendiente</span>
                      <button
                        type="button"
                        class="foto-quitar"
                        title="Quitar foto"
                        @click="quitarFotoPendiente(fila.criterio.id, idx)"
                      >
                        ×
                      </button>
                    </div>
                  </div>
                </div>
                <div class="hallazgo-acciones">
                  <button
                    class="btn small"
                    :disabled="soloLectura || hallazgosGuardando[fila.criterio.id]"
                    @click="guardarHallazgo(fila.criterio)"
                  >
                    {{
                      fila.criterio.hallazgo_id
                        ? 'Actualizar hallazgo'
                        : 'Registrar hallazgo'
                    }}
                  </button>
                  <button
                    v-if="fila.criterio.hallazgo_id && !soloLectura"
                    class="btn small danger"
                    @click="quitarHallazgo(fila.criterio)"
                  >
                    Quitar hallazgo
                  </button>
                </div>
                <div v-if="hallazgosError[fila.criterio.id]" class="msg error small">
                  {{ hallazgosError[fila.criterio.id] }}
                </div>
                <div v-else-if="fila.criterio.hallazgo_id" class="msg success small">
                  Hallazgo #{{ fila.criterio.hallazgo_id }} registrado.
                </div>
              </div>
            </div>
            <div
              v-if="fila.criterio.respuesta_valor && fila.criterio.respuesta_valor !== 'V' && !mostrarCampoHallazgo(fila.criterio) && !esCumplimiento()"
              class="criterio-obs"
            >
              <input
                v-model="fila.criterio.respuesta_observaciones"
                class="input"
                placeholder="Observaciones..."
                type="text"
                :disabled="soloLectura"
              />
            </div>
          </div>
        </template>
      </div>

      <div class="acciones">
        <button
          class="btn"
          :disabled="cargando || bloqueado"
          @click="guardar"
        >Guardar</button>
        <button
          class="btn primary"
          :disabled="cargando || respondidos < total || bloqueado"
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
.audit-docket {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  margin-bottom: 1.25rem;
  padding: 1rem 1.15rem;
  background: var(--c-surface, #fff);
  border: 1px solid var(--c-line, #e6e9ef);
  border-radius: var(--r-lg, 14px);
}

.audit-docket--sticky {
  position: sticky;
  top: 3.8rem;
  z-index: 30;
}

.docket-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
}

.docket-id {
  flex: 1;
  min-width: 0;
}

.docket-title-row {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  flex-wrap: wrap;
}

.docket-title {
  font-size: var(--text-2xl, 1.625rem);
  line-height: 1.15;
  letter-spacing: -0.03em;
  color: var(--c-ink, #0f172a);
  text-wrap: balance;
}

.docket-status {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.2rem 0.55rem;
  border-radius: var(--r-pill, 999px);
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  white-space: nowrap;
}

.docket-status--final {
  color: var(--c-ok-ink, #166534);
  background: var(--c-ok-soft, #dcfce7);
}

.docket-status--pending {
  color: var(--c-warn-ink, #92400e);
  background: var(--c-warn-soft, #fef3c7);
}

.docket-status--muted {
  color: var(--c-ink-3, #64748b);
  background: var(--c-surface-3, #f1f5f9);
}

.status-dot {
  width: 0.4rem;
  height: 0.4rem;
  border-radius: 50%;
  background: currentColor;
}

.docket-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem 1rem;
  margin-top: 0.45rem;
  color: var(--c-ink-3, #64748b);
  font-size: 0.8rem;
}

.docket-meta-item {
  display: inline-flex;
  align-items: center;
  gap: 0.32rem;
}

.docket-meta-item svg {
  width: 0.9rem;
  height: 0.9rem;
  color: var(--c-ink-4, #94a3b8);
}

.docket-progress {
  width: 280px;
  flex-shrink: 0;
}

.docket-progress-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.45rem;
}

.docket-progress-label {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--c-ink-3, #64748b);
}

.docket-progress-value {
  display: inline-flex;
  align-items: baseline;
  gap: 0.05rem;
  font-variant-numeric: tabular-nums;
  color: var(--c-ink-3, #64748b);
}

.docket-progress-value strong {
  font-size: 1.35rem;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.03em;
  color: var(--c-ink, #0f172a);
}

.docket-progress-value span {
  font-size: 0.8rem;
  font-weight: 600;
}

.docket-track {
  display: flex;
  gap: 3px;
  height: 10px;
}

.docket-seg {
  flex: 1 1 0;
  min-width: 2px;
  border-radius: 2px;
  background: var(--c-line, #e6e9ef);
  transition: background-color 0.2s var(--ease), transform 0.2s var(--ease);
}

.docket-seg.is-done {
  background: var(--c-primary, #2563eb);
}

.docket-seg.is-done:hover {
  transform: scaleY(1.25);
}

.pendiente-aviso {
  padding: 0.75rem 0.95rem;
  border-radius: var(--r-md, 10px);
  background: var(--c-warn-soft, #fef3c7);
  border: 1px solid #fcd34d;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.pendiente-aviso p {
  margin: 0;
  font-size: 0.85rem;
  color: var(--c-warn-ink, #92400e);
}

@media (max-width: 720px) {
  .audit-docket {
    padding: 0.85rem 0.9rem;
  }

  .docket-main {
    flex-direction: column;
    align-items: stretch;
    gap: 0.8rem;
  }

  .docket-title {
    font-size: var(--text-lg, 1.0625rem);
  }

  .docket-meta {
    gap: 0.3rem 0.8rem;
    font-size: 0.76rem;
  }

  .docket-progress {
    width: 100%;
  }
}

/* --- Checklist --- */
.criterios {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.criterio-head {
  font-weight: 700;
  line-height: 1.35;
  color: var(--c-ink, #0f172a);
}

.criterio-head--seccion {
  margin-top: 1.25rem;
  padding: 0.6rem 0.9rem;
  border-radius: var(--r-md, 10px);
  background: var(--c-surface-3, #f1f5f9);
  font-size: 0.95rem;
  letter-spacing: 0.01em;
}

.criterio-head--seccion:first-child {
  margin-top: 0;
}

.criterio-head--subseccion {
  margin-top: 0.9rem;
  padding-left: 0.9rem;
  font-size: 0.86rem;
  color: var(--c-ink-2, #334155);
}

.criterio-head--subtitulo {
  margin-top: 0.7rem;
  padding-left: 0.9rem;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--c-ink-3, #64748b);
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

.chip-btn.neutro {
  color: var(--c-ink-3, #64748b);
  border-color: var(--c-ink-4, #94a3b8);
}

.chip-btn.neutro.activo {
  background: var(--c-ink-3, #64748b);
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
  background: var(--c-surface, #fff);
}

.criterio-hallazgo label {
  display: block;
  margin-bottom: 0.4rem;
  font-size: 0.85rem;
}

.criterio-hallazgo label strong {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  color: var(--c-ink, #0f172a);
}

.criterio-hallazgo label strong::before {
  content: '';
  width: 0.45rem;
  height: 0.45rem;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--c-ink-4, #94a3b8);
}

.criterio-hallazgo.amarillo label strong {
  color: var(--c-warn-ink, #92400e);
}

.criterio-hallazgo.amarillo label strong::before {
  background: var(--c-warn, #d97706);
}

.criterio-hallazgo.rojo label strong {
  color: var(--c-danger-ink, #b91c1c);
}

.criterio-hallazgo.rojo label strong::before {
  background: var(--c-danger, #dc2626);
}

.hallazgo-area {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  margin-bottom: 0.6rem;
}

.hallazgo-area span {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--c-ink-2, #334155);
}

.hallazgo-area select {
  width: 100%;
  box-sizing: border-box;
}

.hallazgo-aviso {
  margin: 0;
  font-size: 0.8rem;
  color: var(--c-ink-3, #64748b);
}

.hallazgo-aviso.err {
  color: var(--c-danger, #dc2626);
}

.hallazgo-responsable {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  padding: 0.45rem 0.6rem;
  border: 1px solid var(--c-line-2, #d5dae3);
  border-radius: 6px;
  background: var(--c-surface-2, #f8fafc);
}

.hallazgo-responsable strong {
  font-size: 0.9rem;
  color: var(--c-ink, #0f172a);
}

.hallazgo-responsable small {
  font-size: 0.75rem;
  color: var(--c-ink-3, #64748b);
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

/* --- Fotos de evidencia --- */
.hallazgo-fotos {
  margin-top: 0.6rem;
}

.foto-add {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.7rem;
  padding: 0.55rem 0.75rem;
  border: 1px dashed var(--c-line-2, #d5dae3);
  border-radius: var(--r-md, 10px);
  background: var(--c-surface, #fff);
  color: var(--c-ink-2, #334155);
  font-family: inherit;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s var(--ease), background 0.15s var(--ease);
}

.foto-add:hover:not(:disabled) {
  border-color: var(--c-primary, #2563eb);
  background: var(--c-primary-soft, #eef2ff);
}

.foto-add:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.foto-add-icon {
  width: 2rem;
  height: 2rem;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--c-surface-3, #f1f5f9);
  color: var(--c-ink-3, #64748b);
  transition: background 0.15s var(--ease), color 0.15s var(--ease);
}

.foto-add:hover:not(:disabled) .foto-add-icon {
  background: var(--c-primary, #2563eb);
  color: #fff;
}

.foto-add-icon svg {
  width: 1.1rem;
  height: 1.1rem;
}

.foto-add-text {
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
  min-width: 0;
}

.foto-add-text strong {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--c-ink-2, #334155);
}

.foto-add-text small {
  font-size: 0.7rem;
  color: var(--c-ink-3, #64748b);
}

.fotos-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.foto-thumb {
  position: relative;
  width: 72px;
  height: 72px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--c-line, #e6e9ef);
  background: var(--c-surface, #fff);
}

.foto-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.foto-thumb.pendiente {
  opacity: 0.85;
  border-style: dashed;
}

.foto-etiqueta {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  font-size: 0.6rem;
  text-align: center;
  background: rgba(15, 23, 42, 0.65);
  color: #fff;
}

.foto-quitar {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: none;
  background: rgba(15, 23, 42, 0.65);
  color: #fff;
  font-size: 0.85rem;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.foto-quitar:hover {
  background: var(--c-danger, #dc2626);
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

@media (prefers-reduced-motion: reduce) {
  .docket-seg {
    transition: none;
  }

  .docket-seg.is-done:hover {
    transform: none;
  }
}
</style>
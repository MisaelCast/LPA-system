interface ErrorAxios {
  isAxiosError?: boolean
  response?: unknown
  code?: string
  message?: string
}

function comoAxios(err: unknown): ErrorAxios | null {
  if (!err || typeof err !== 'object') return null
  const error = err as ErrorAxios
  if (!error.isAxiosError) return null
  return error
}

/** true cuando la petición no obtuvo respuesta (fallo de red/timeout). */
export function esErrorDeRed(err: unknown): boolean {
  const error = comoAxios(err)
  if (!error) return false
  if (error.response) return false
  if (error.code === 'ERR_NETWORK' || error.code === 'ECONNABORTED') {
    return true
  }
  return /network error|timeout/i.test(error.message ?? '')
}

/**
 * Reintenta una operación asíncrona solo ante errores de red.
 * Los errores con respuesta HTTP se propagan de inmediato.
 */
export async function conReintento<T>(
  operacion: () => Promise<T>,
  opciones: { intentos?: number; esperaMs?: number } = {},
): Promise<T> {
  const intentos = Math.max(1, opciones.intentos ?? 3)
  const esperaMs = Math.max(0, opciones.esperaMs ?? 600)
  let ultimoError: unknown
  for (let intento = 0; intento < intentos; intento += 1) {
    try {
      return await operacion()
    } catch (err) {
      ultimoError = err
      if (intento === intentos - 1 || !esErrorDeRed(err)) {
        throw err
      }
      await new Promise((resolve) => {
        window.setTimeout(resolve, esperaMs * (intento + 1))
      })
    }
  }
  throw ultimoError
}

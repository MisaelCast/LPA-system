const TIPOS_ACEPTADOS = [
  'image/jpeg',
  'image/png',
  'image/webp',
  'image/heic',
  'image/heif',
]

const EXTENSIONES_VALIDAS = /\.(jpe?g|png|webp|heic|heif)$/i
const TAMANO_MAXIMO = 5 * 1024 * 1024
const LADO_MAXIMO = 1920
const CALIDADES = [0.85, 0.75, 0.62]

/** Valor para el atributo ``accept`` de los inputs de imagen. */
export const ACEPTA_IMAGENES =
  'image/jpeg,image/png,image/webp,image/heic,image/heif'

export function esTipoImagenValido(archivo: File): boolean {
  const tipo = (archivo.type || '').toLowerCase()
  if (TIPOS_ACEPTADOS.includes(tipo)) return true
  return EXTENSIONES_VALIDAS.test(archivo.name || '')
}

interface ImagenDecodificada {
  fuente: CanvasImageSource
  ancho: number
  alto: number
  liberar: () => void
}

async function decodificar(archivo: File): Promise<ImagenDecodificada> {
  if (typeof createImageBitmap === 'function') {
    try {
      const bitmap = await createImageBitmap(archivo, {
        imageOrientation: 'from-image',
      })
      return {
        fuente: bitmap,
        ancho: bitmap.width,
        alto: bitmap.height,
        liberar: () => bitmap.close(),
      }
    } catch {
      // Algunos navegadores no decodifican HEIC con createImageBitmap;
      // se intenta con <img> (iOS Safari sí lo soporta).
    }
  }

  const url = URL.createObjectURL(archivo)
  try {
    const imagen = await new Promise<HTMLImageElement>((resolve, reject) => {
      const elemento = new Image()
      elemento.onload = () => resolve(elemento)
      elemento.onerror = () =>
        reject(new Error('No se pudo leer la imagen.'))
      elemento.src = url
    })
    return {
      fuente: imagen,
      ancho: imagen.naturalWidth,
      alto: imagen.naturalHeight,
      liberar: () => URL.revokeObjectURL(url),
    }
  } catch (err) {
    URL.revokeObjectURL(url)
    throw err
  }
}

async function aJpeg(
  fuente: CanvasImageSource,
  ancho: number,
  alto: number,
  calidad: number,
): Promise<Blob> {
  const lienzo = document.createElement('canvas')
  lienzo.width = ancho
  lienzo.height = alto
  const contexto = lienzo.getContext('2d')
  if (!contexto) {
    throw new Error('No se pudo procesar la imagen.')
  }
  contexto.fillStyle = '#ffffff'
  contexto.fillRect(0, 0, ancho, alto)
  contexto.drawImage(fuente, 0, 0, ancho, alto)
  return new Promise<Blob>((resolve, reject) => {
    lienzo.toBlob(
      (blob) => {
        if (blob) resolve(blob)
        else reject(new Error('No se pudo procesar la imagen.'))
      },
      'image/jpeg',
      calidad,
    )
  })
}

/**
 * Normaliza una foto para subirla como evidencia: la decodifica (incluye
 * HEIC cuando el navegador lo soporta), la redimensiona y la recomprime a
 * JPEG para garantizar que no supere los 5 MB.
 */
export async function procesarImagenParaSubida(archivo: File): Promise<File> {
  if (!esTipoImagenValido(archivo)) {
    throw new Error('Formato no permitido. Usa archivos JPG, PNG o WEBP.')
  }

  let imagen: ImagenDecodificada
  try {
    imagen = await decodificar(archivo)
  } catch {
    throw new Error(
      'No se pudo procesar la imagen. Si es HEIC, cambia la cámara a JPG o elige otra foto.',
    )
  }

  try {
    const escala = Math.min(
      1,
      LADO_MAXIMO / Math.max(imagen.ancho, imagen.alto),
    )
    let ancho = Math.max(1, Math.round(imagen.ancho * escala))
    let alto = Math.max(1, Math.round(imagen.alto * escala))

    let blob: Blob | null = null
    for (const calidad of CALIDADES) {
      blob = await aJpeg(imagen.fuente, ancho, alto, calidad)
      if (blob.size <= TAMANO_MAXIMO) break
      if (calidad === CALIDADES[CALIDADES.length - 1] && blob.size > TAMANO_MAXIMO) {
        const factor = Math.sqrt(TAMANO_MAXIMO / blob.size) * 0.95
        ancho = Math.max(1, Math.round(ancho * factor))
        alto = Math.max(1, Math.round(alto * factor))
        blob = await aJpeg(imagen.fuente, ancho, alto, calidad)
      }
    }

    if (!blob) {
      throw new Error('No se pudo procesar la imagen.')
    }
    if (blob.size > TAMANO_MAXIMO) {
      throw new Error(
        'La imagen sigue superando los 5 MB incluso después de comprimirla.',
      )
    }

    const nombreBase = (archivo.name || 'imagen').replace(/\.[^.]+$/, '')
    return new File([blob], `${nombreBase || 'imagen'}.jpg`, {
      type: 'image/jpeg',
      lastModified: Date.now(),
    })
  } finally {
    imagen.liberar()
  }
}

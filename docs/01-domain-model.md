# Modelo de Dominio

## Objetivo

Este documento describe las entidades principales del negocio del Sistema LPA y la forma en que se relacionan entre sí.

No representa el diseño de la base de datos.

> **Estado (actualizado al código vigente):** este modelo incluye el rol
> **Responsable de Manufactura**, el ciclo completo de **tickets de hallazgo**
> (asignación, avance, solicitud y resolución de cierre con historial) y la
> **programación semanal / días hábiles** de auditorías. Refleja la
> implementación actual; no es un modelo preliminar.

---

# Área

## Descripción

Representa un área de producción donde el Departamento de Calidad realiza auditorías.

## Ejemplos

- Ensamble Final
- Pulido

## Responsabilidades

- Identificar dónde se realiza una auditoría.
- Agrupar las auditorías correspondientes a esa área.

## Relaciones

- Puede tener cero o varias células.
- Puede tener una o varias auditorías.

---

# Célula

## Descripción

Representa una línea o célula de producción dentro de un área.

No todas las áreas utilizan células.

## Ejemplos

Ensamble Final

- Célula 1
- Célula 2
- ...
- Célula 7

Pulido

- Célula A
- Célula B

## Responsabilidades

- Identificar el lugar específico donde se ejecuta una auditoría.

## Relaciones

- Pertenece a un Área.
- Puede estar asociada a múltiples ejecuciones de auditoría.

---

# Capa

## Descripción

Representa el nivel jerárquico dentro del proceso LPA.

## Capas

- Auditor
- Supervisor
- Gerente

> Las **capas** describen el nivel jerárquico de la auditoría. Los **roles de
> usuario** son independientes de la capa; además de Auditor, Supervisor y
> Gerente incluyen Administrador y Responsable de Manufactura (ver Usuario).

## Responsabilidades

Determinar el tipo de auditoría que debe realizarse.

## Relaciones

- Una capa puede tener una o varias auditorías.

---

# Auditoría

## Descripción

Define una auditoría disponible dentro del sistema.

Una auditoría contiene los criterios que deben verificarse.

Cada auditoría pertenece a una capa y, cuando aplica, a un área específica.

## Ejemplos

- Auditoría Ensamble Final
- Auditoría Pulido
- Auditoría Supervisor
- Auditoría Gerente

## Responsabilidades

- Definir los criterios de evaluación.
- Definir la frecuencia de ejecución.
- Determinar la capa responsable.
- Definir el **tipo de respuesta**: `semaforo` (V/A/R) o `cumplimiento`
  (`cumple`/`no_cumple`/`na`).
- Definir su **programación**: sorteo semanal o días hábiles elegidos.

## Relaciones

- Pertenece a una Capa.
- Puede pertenecer a un Área.
- Contiene múltiples criterios.
- Puede ejecutarse múltiples veces.
- Puede tener cero o varios días hábiles elegidos.
- Puede participar en la programación semanal.

---

# Programación de auditorías

## Programación semanal (sorteo)

Cada semana se asigna, por sorteo, una auditoría a cada día hábil (lunes a
viernes). El calendario se genera una sola vez por semana y se conserva para
trazabilidad; las semanas anteriores no se reprograman. Aplica a las
auditorías marcadas con `programacion_semanal`.

## Días hábiles elegidos

Una auditoría puede definir uno o varios días hábiles fijos (lunes a viernes).
En ese caso se ejecuta cada semana en esos días, dentro del periodo de su
frecuencia, y no participa en el sorteo semanal.

## Relaciones

- Una auditoría puede tener cero o varios días hábiles elegidos.
- Una semana contiene una asignación por día hábil (una auditoría por día).

---

# Criterio

## Descripción

Representa un punto de inspección dentro de una auditoría.

Cada criterio corresponde a un aspecto que debe verificarse durante la ejecución.

## Ejemplos

- Se realiza la inspección Check Do Check.
- La estación de trabajo se mantiene limpia.
- Se realiza la prueba de sonido.

## Responsabilidades

Definir qué debe inspeccionarse durante una auditoría.

## Relaciones

- Pertenece a una Auditoría.
- Puede tener múltiples respuestas a lo largo del tiempo.

---

# Ejecución de Auditoría

## Descripción

Representa una auditoría realizada por un usuario en una fecha determinada.

Cada ejecución conserva su propio historial de respuestas.

## Responsabilidades

- Registrar quién realizó la auditoría.
- Registrar la fecha.
- Registrar observaciones generales.
- Conservar el historial.

## Relaciones

- Pertenece a una Auditoría.
- Es realizada por un Usuario.
- Contiene múltiples respuestas.
- Puede generar hallazgos.

---

# Respuesta

## Descripción

Representa el resultado obtenido para un criterio durante una ejecución de auditoría.

## Valores posibles

Dependen del tipo de respuesta definido en la auditoría:

- **Semáforo:** `V` (verde / cumple), `A` (amarillo / observación menor) y
  `R` (rojo / hallazgo mayor).
- **Cumplimiento:** `cumple`, `no_cumple` y `na` (no aplica).

Solo `A`, `R` y `no_cumple` pueden generar un hallazgo.

## Responsabilidades

Registrar el resultado observado para cada criterio.

## Relaciones

- Pertenece a una Ejecución de Auditoría.
- Pertenece a un Criterio.
- Puede generar un Hallazgo.

---

# Hallazgo (ticket)

## Descripción

Representa una desviación detectada durante una auditoría y, a partir de su
registro, un **ticket de corrección** que se atiende hasta su cierre.

Se registra sobre respuestas con valor `A`, `R` o `no_cumple`. No toda
respuesta no conforme genera un hallazgo; su registro depende del criterio del
auditor.

## Datos principales

- Descripción y tipo (derivado del valor de la respuesta).
- Área responsable y **Responsable de Manufactura** asignado.
- **Fecha límite** de corrección (para detectar atrasos).
- Acción correctiva, estado y fecha de cierre.
- Evidencias originales y de corrección.

## Estados del ticket

- `abierto`: registrado y pendiente de atención.
- `en_correccion`: el responsable registró un avance.
- `cierre_solicitado`: el responsable solicita la validación del cierre.
- `cerrado`: el auditor aprueba el cierre.

## Flujo de atención

1. El **Auditor** registra el hallazgo, asigna al Responsable de Manufactura
   del área y define la fecha límite (o se calcula un plazo por defecto).
2. El **Responsable de Manufactura** registra avances (acción correctiva o
   comentario) y solicita el cierre cuando termina la corrección. Puede adjuntar
   evidencia de corrección.
3. El **Auditor dueño** (o un Administrador) aprueba o rechaza el cierre. Si lo
   rechaza, el ticket vuelve a `en_correccion` conservando el historial.
4. El responsable no puede aprobar el cierre de su propio hallazgo.

## Responsabilidades

- Registrar la desviación y su contexto.
- Asociar evidencia original y de corrección.
- Asignar responsables y fecha límite.
- Mantener la trazabilidad del ticket mediante historial inmutable.

## Relaciones

- Pertenece a una Respuesta.
- Puede tener múltiples evidencias (original/corrección).
- Tiene un Responsable de Manufactura asignado (N:M).
- Tiene múltiples entradas de historial (HallazgoSeguimiento).

---

# HallazgoSeguimiento

## Descripción

Entrada inmutable del historial de un hallazgo (ticket). Cada asignación,
comentario, avance, solicitud o resolución de cierre agrega una fila; el
historial nunca se sobrescribe.

## Datos

- Tipo: `asignacion`, `comentario`, `accion_correctiva`, `estado`,
  `solicitud_cierre`, `cierre_aprobado` o `cierre_rechazado`.
- Usuario que realizó la acción, detalle y fecha.
- Estado anterior y nuevo (trazabilidad de transiciones).

## Relaciones

- Pertenece a un Hallazgo.
- Registra al Usuario que actuó.

---

# Evidencia

## Descripción

Representa archivos asociados a un hallazgo. Actualmente se manejan fotografías
JPG/PNG/WEBP (máximo 5 MB), almacenadas en Supabase Storage.

## Tipos

- `original`: evidencia del hallazgo al momento de detectarlo.
- `correccion`: evidencia del trabajo de corrección del responsable.

## Responsabilidades

Documentar visualmente un hallazgo y su corrección.

## Relaciones

- Pertenece a un Hallazgo.

---

# Usuario

## Descripción

Representa una persona que utiliza el sistema.

## Roles

- Administrador
- Auditor
- Supervisor
- Gerente
- **Responsable de Manufactura**

El Responsable de Manufactura atiende los hallazgos de su área: registra
avances, adjunta evidencia de corrección y solicita el cierre del ticket. No
puede aprobar el cierre de su propio hallazgo.

## Responsabilidades

- Iniciar sesión.
- Ejecutar auditorías (Auditor).
- Registrar y resolver hallazgos (Auditor/Administrador).
- Atender tickets de hallazgo (Responsable de Manufactura).
- Consultar información según su rol y ámbito.

## Relaciones

- Puede estar asignado a múltiples áreas.
- Puede estar a cargo de una o varias células.
- Puede realizar múltiples ejecuciones de auditoría.
- Puede ser responsable de múltiples hallazgos.
- Puede tener múltiples entradas de historial (HallazgoSeguimiento).

---

# Relaciones del dominio

Área
├── contiene Células
├── agrupa Auditorías
└── es área responsable de Hallazgos

Capa ── 1:N ── Auditoría ── 1:N ── Criterio
                    │
                    ├── 1:N ── Ejecución de Auditoría ── 1:N ── Respuesta
                    │                                              │
                    │                                              ▼
                    │                                          Hallazgo
                    │                                              │
                    │                 ┌────────────────────────────┼──────────────────────┐
                    │                 ▼                            ▼                      ▼
                    │            Evidencia                 HallazgoSeguimiento   Responsable de
                    │        (original/corrección)            (historial)        Manufactura (N:M)
                    │
                    ├── 1:N ── AuditoriaDia (días hábiles elegidos)
                    └── 1:N ── ProgramacionSemanal (sorteo por semana y día)

Usuario
├── realiza Ejecuciones de Auditoría (Auditor)
├── atiende Hallazgos (Responsable de Manufactura)
└── registra HallazgoSeguimiento

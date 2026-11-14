# Esquema de Base de Datos

## Objetivo

Este documento describe el diseño físico de la base de datos del Sistema LPA: las tablas, columnas, restricciones y relaciones tal como existen tras aplicar todas las migraciones de Alembic.

Complementa a [Modelo de Dominio](./01-domain-model.md), que describe el negocio y no el diseño de la base de datos.

> **Estado (actualizado al código vigente):** el esquema consta de **19 tablas**.
> La última revisión de Alembic es `f1a2b3c4d5e6` e incluye
> `hallazgo_seguimiento`, `programacion_semanal` y `auditoria_dia`, además de
> las columnas `hallazgo.fecha_limite`, `evidencia.tipo` y
> `auditoria.programacion_semanal`. Estas funcionalidades están implementadas;
> el documento se actualiza para evitar que una versión anterior se interprete
> como ausencia de implementación.

| Dato | Valor |
| --- | --- |
| Motor | PostgreSQL |
| ORM | SQLModel (SQLAlchemy + Pydantic) |
| Modelos | `backend/app/models/` |
| Migraciones | `backend/migrations/versions/` |
| Tablas | 19 |
| Última revisión | `f1a2b3c4d5e6` |

---

## Tablas

| # | Tabla | Descripción |
| --- | --- | --- |
| 1 | `area` | Área de producción donde se realizan auditorías. |
| 2 | `capa` | Nivel jerárquico dentro del proceso LPA. |
| 3 | `frecuencia` | Periodicidad con la que debe ejecutarse una auditoría. |
| 4 | `rol` | Rol de acceso asignado a un usuario. |
| 5 | `usuario` | Persona que utiliza el sistema LPA. |
| 6 | `auditoria` | Auditoría disponible dentro del sistema. |
| 7 | `auditoria_dia` | Días hábiles elegidos para la recurrencia semanal de una auditoría. |
| 8 | `programacion_semanal` | Asignación semanal de auditorías por sorteo (lunes a viernes). |
| 9 | `celula` | Línea o célula de producción dentro de un área. |
| 10 | `criterio` | Punto de inspección dentro de una auditoría. |
| 11 | `ejecucion_auditoria` | Auditoría realizada por un usuario en una fecha. |
| 12 | `respuesta` | Resultado observado para un criterio durante una ejecución. |
| 13 | `hallazgo` | Desviación detectada durante una auditoría (ticket de corrección). |
| 14 | `hallazgo_responsable` | Tabla intermedia N:M entre hallazgo y usuario responsable. |
| 15 | `hallazgo_seguimiento` | Historial inmutable de acciones y transiciones del hallazgo. |
| 16 | `evidencia` | Archivo asociado a un hallazgo (original o de corrección). |
| 17 | `usuario_area` | Tabla intermedia N:M entre usuario y área. |
| 18 | `usuario_celula` | Tabla intermedia N:M entre usuario y célula a cargo. |
| 19 | `usuario_supervisor` | Tabla intermedia N:M entre gerente y supervisores a cargo. |

---

## Esquema SQL (DDL final)

```sql
-- area: Área de producción donde se realizan auditorías.
CREATE TABLE area (
    id           SERIAL       PRIMARY KEY,
    nombre       VARCHAR(150) NOT NULL,
    descripcion  VARCHAR(255),
    activa       BOOLEAN      NOT NULL DEFAULT TRUE
);
CREATE UNIQUE INDEX ix_area_nombre ON area (nombre);

-- capa: Nivel jerárquico dentro del proceso LPA.
CREATE TABLE capa (
    id              SERIAL       PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    descripcion     VARCHAR(255),
    activa          BOOLEAN      NOT NULL DEFAULT TRUE,
    requiere_celula BOOLEAN      NOT NULL DEFAULT TRUE
);
CREATE UNIQUE INDEX ix_capa_nombre ON capa (nombre);

-- frecuencia: Periodicidad con la que debe ejecutarse una auditoría.
CREATE TABLE frecuencia (
    id           SERIAL       PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL,
    descripcion  VARCHAR(255),
    dias         INTEGER      NOT NULL
);
CREATE UNIQUE INDEX ix_frecuencia_nombre ON frecuencia (nombre);

-- rol: Rol de acceso asignado a un usuario.
CREATE TABLE rol (
    id           SERIAL       PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL,
    descripcion  VARCHAR(255)
);
CREATE UNIQUE INDEX ix_rol_nombre ON rol (nombre);

-- usuario: Persona que utiliza el sistema LPA.
CREATE TABLE usuario (
    id              SERIAL       PRIMARY KEY,
    nombre          VARCHAR(150) NOT NULL,
    correo          VARCHAR(255) NOT NULL,
    contrasena_hash VARCHAR(255) NOT NULL,
    activo          BOOLEAN      NOT NULL DEFAULT TRUE,
    rol_id          INTEGER      NOT NULL REFERENCES rol (id)
);
CREATE UNIQUE INDEX ix_usuario_correo ON usuario (correo);

-- auditoria: Auditoría disponible dentro del sistema.
CREATE TABLE auditoria (
    id            SERIAL       PRIMARY KEY,
    nombre        VARCHAR(150) NOT NULL,
    descripcion   VARCHAR(500),
    activa        BOOLEAN      NOT NULL DEFAULT TRUE,
    tipo_respuesta VARCHAR(20)  NOT NULL DEFAULT 'semaforo',
    dia_semana   INTEGER,
    programacion_semanal BOOLEAN NOT NULL DEFAULT FALSE,
    capa_id       INTEGER      NOT NULL REFERENCES capa (id),
    frecuencia_id INTEGER      NOT NULL REFERENCES frecuencia (id),
    area_id       INTEGER      REFERENCES area (id)
);
CREATE INDEX ix_auditoria_nombre ON auditoria (nombre);

-- auditoria_dia: Días hábiles elegidos para la recurrencia semanal.
CREATE TABLE auditoria_dia (
    id           SERIAL  PRIMARY KEY,
    auditoria_id INTEGER NOT NULL REFERENCES auditoria (id),
    dia_semana   INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 4),
    CONSTRAINT uq_auditoria_dia UNIQUE (auditoria_id, dia_semana)
);
CREATE INDEX ix_auditoria_dia_auditoria_id ON auditoria_dia (auditoria_id);

-- programacion_semanal: Sorteo de auditorías por semana y día hábil.
CREATE TABLE programacion_semanal (
    id            SERIAL  PRIMARY KEY,
    semana_inicio DATE    NOT NULL,
    dia_semana    INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 4),
    auditoria_id  INTEGER NOT NULL REFERENCES auditoria (id),
    CONSTRAINT uq_programacion_semanal_semana_dia
        UNIQUE (semana_inicio, dia_semana)
);
CREATE INDEX ix_programacion_semanal_semana_inicio
    ON programacion_semanal (semana_inicio);

-- celula: Línea o célula de producción dentro de un área.
CREATE TABLE celula (
    id      SERIAL  PRIMARY KEY,
    numero  INTEGER NOT NULL,
    activa  BOOLEAN NOT NULL DEFAULT TRUE,
    area_id INTEGER NOT NULL REFERENCES area (id),
    CONSTRAINT celula_area_id_numero_key UNIQUE (area_id, numero)
);

-- criterio: Punto de inspección dentro de una auditoría.
CREATE TABLE criterio (
    id           SERIAL       PRIMARY KEY,
    descripcion  VARCHAR(500) NOT NULL,
    orden        INTEGER      NOT NULL DEFAULT 1,
    activo       BOOLEAN      NOT NULL DEFAULT TRUE,
    auditoria_id INTEGER      NOT NULL REFERENCES auditoria (id),
    seccion      VARCHAR(150),
    subseccion   VARCHAR(150),
    subtitulo    VARCHAR(150)
);

-- ejecucion_auditoria: Auditoría realizada por un usuario en una fecha.
CREATE TABLE ejecucion_auditoria (
    id               SERIAL        PRIMARY KEY,
    fecha            TIMESTAMP     NOT NULL,
    fecha_programada TIMESTAMP WITH TIME ZONE,
    observaciones    VARCHAR(1000),
    estado           VARCHAR(20)   NOT NULL DEFAULT 'en_proceso',
    auditoria_id     INTEGER       NOT NULL REFERENCES auditoria (id),
    usuario_id       INTEGER       NOT NULL REFERENCES usuario (id),
    celula_id        INTEGER       REFERENCES celula (id)
);

-- respuesta: Resultado observado para un criterio durante una ejecución.
CREATE TABLE respuesta (
    id                     SERIAL       PRIMARY KEY,
    valor                  VARCHAR(20)  NOT NULL,
    observaciones          VARCHAR(1000),
    ejecucion_auditoria_id INTEGER      NOT NULL REFERENCES ejecucion_auditoria (id),
    criterio_id            INTEGER      NOT NULL REFERENCES criterio (id),
    CONSTRAINT uq_respuesta_ejecucion_criterio
        UNIQUE (ejecucion_auditoria_id, criterio_id)
);

-- hallazgo: Desviación detectada durante una auditoría (ticket).
-- estado: abierto | en_correccion | cierre_solicitado | cerrado
CREATE TABLE hallazgo (
    id                  SERIAL        PRIMARY KEY,
    descripcion         VARCHAR(1000) NOT NULL,
    fecha_creacion      TIMESTAMP     NOT NULL,
    respuesta_id        INTEGER       NOT NULL REFERENCES respuesta (id),
    estado              VARCHAR(20)   NOT NULL DEFAULT 'abierto',
    accion_correctiva   VARCHAR(1000),
    area_responsable_id INTEGER       REFERENCES area (id),
    fecha_limite        TIMESTAMP,
    fecha_cierre        TIMESTAMP WITH TIME ZONE,
    CONSTRAINT hallazgo_respuesta_id_key UNIQUE (respuesta_id)
);

-- evidencia: Archivo asociado a un hallazgo (original o de corrección).
CREATE TABLE evidencia (
    id           SERIAL       PRIMARY KEY,
    ruta_archivo VARCHAR(500) NOT NULL,
    tipo_archivo VARCHAR(100) NOT NULL DEFAULT 'fotografia',
    tipo         VARCHAR(20)  NOT NULL DEFAULT 'original',
    fecha_carga  TIMESTAMP    NOT NULL,
    hallazgo_id  INTEGER      NOT NULL REFERENCES hallazgo (id)
);

-- hallazgo_seguimiento: Historial inmutable de acciones y transiciones.
CREATE TABLE hallazgo_seguimiento (
    id             SERIAL        PRIMARY KEY,
    hallazgo_id    INTEGER       NOT NULL REFERENCES hallazgo (id),
    usuario_id     INTEGER       NOT NULL REFERENCES usuario (id),
    tipo           VARCHAR(30)   NOT NULL,
    detalle        VARCHAR(1000),
    estado_desde   VARCHAR(20),
    estado_hasta   VARCHAR(20),
    fecha_creacion TIMESTAMP     NOT NULL DEFAULT now()
);
CREATE INDEX ix_hallazgo_seguimiento_hallazgo_id
    ON hallazgo_seguimiento (hallazgo_id);

-- usuario_area: Asigna usuarios a las áreas donde pueden operar (N:M).
CREATE TABLE usuario_area (
    usuario_id INTEGER NOT NULL REFERENCES usuario (id),
    area_id    INTEGER NOT NULL REFERENCES area (id),
    PRIMARY KEY (usuario_id, area_id)
);

-- usuario_celula: Asigna usuarios a las células a cargo (N:M).
CREATE TABLE usuario_celula (
    usuario_id INTEGER NOT NULL REFERENCES usuario (id),
    celula_id  INTEGER NOT NULL REFERENCES celula (id),
    PRIMARY KEY (usuario_id, celula_id)
);

-- usuario_supervisor: Supervisores a cargo de un gerente (N:M).
CREATE TABLE usuario_supervisor (
    gerente_id    INTEGER NOT NULL REFERENCES usuario (id),
    supervisor_id INTEGER NOT NULL REFERENCES usuario (id),
    PRIMARY KEY (gerente_id, supervisor_id)
);

-- hallazgo_responsable: Usuarios responsables de atender hallazgos (N:M).
CREATE TABLE hallazgo_responsable (
    hallazgo_id INTEGER NOT NULL REFERENCES hallazgo (id),
    usuario_id  INTEGER NOT NULL REFERENCES usuario (id),
    PRIMARY KEY (hallazgo_id, usuario_id)
);
```

---

## Relaciones

```text
rol                  1 --- N  usuario
area                 1 --- N  celula
area                 1 --- N  auditoria
area                 N --- N  usuario              (via usuario_area)
celula               N --- N  usuario              (via usuario_celula)
usuario (gerente)    N --- N  usuario (supervisor) (via usuario_supervisor)
capa                 1 --- N  auditoria
frecuencia           1 --- N  auditoria
auditoria            1 --- N  auditoria_dia        (días hábiles elegidos)
auditoria            1 --- N  programacion_semanal (sorteo semanal)
auditoria            1 --- N  criterio
auditoria            1 --- N  ejecucion_auditoria
celula               1 --- N  ejecucion_auditoria
usuario              1 --- N  ejecucion_auditoria
ejecucion_auditoria  1 --- N  respuesta
criterio             1 --- N  respuesta
respuesta            1 --- 1  hallazgo
hallazgo             1 --- N  evidencia
hallazgo             N --- N  usuario              (via hallazgo_responsable)
hallazgo             1 --- N  hallazgo_seguimiento (historial)
usuario              1 --- N  hallazgo_seguimiento (autor de la acción)
area                 1 --- N  hallazgo             (area_responsable)
```

---

## Modelos SQLModel

### `area` — `backend/app/models/area.py`

```python
class Area(SQLModel, table=True):
    """Area de produccion donde se realizan auditorias."""

    __tablename__ = "area"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=150, unique=True, index=True)
    descripcion: str | None = Field(default=None, max_length=255)
    activa: bool = Field(default=True)

    celulas: list["Celula"] = Relationship(back_populates="area")
    auditorias: list["Auditoria"] = Relationship(back_populates="area")
    usuarios: list["Usuario"] = Relationship(
        back_populates="areas",
        link_model=UsuarioArea,
    )
```

### `capa` — `backend/app/models/capa.py`

```python
class Capa(SQLModel, table=True):
    """Nivel jerarquico dentro del proceso LPA."""

    __tablename__ = "capa"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100, unique=True, index=True)
    descripcion: str | None = Field(default=None, max_length=255)
    activa: bool = Field(default=True)
    requiere_celula: bool = Field(default=True)

    auditorias: list["Auditoria"] = Relationship(back_populates="capa")
```

### `frecuencia` — `backend/app/models/frecuencia.py`

```python
class Frecuencia(SQLModel, table=True):
    """Periodicidad con la que debe ejecutarse una auditoria."""

    __tablename__ = "frecuencia"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100, unique=True, index=True)
    descripcion: str | None = Field(default=None, max_length=255)
    dias: int = Field(ge=1)

    auditorias: list["Auditoria"] = Relationship(back_populates="frecuencia")
```

### `rol` — `backend/app/models/rol.py`

```python
class Rol(SQLModel, table=True):
    """Rol de acceso asignado a un usuario."""

    __tablename__ = "rol"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100, unique=True, index=True)
    descripcion: str | None = Field(default=None, max_length=255)

    usuarios: list["Usuario"] = Relationship(back_populates="rol")
```

> Roles sembrados por defecto: `Administrador`, `Gerente`, `Supervisor`,
> `Auditor` y `Responsable de Manufactura`.

### `usuario` — `backend/app/models/usuario.py`

```python
class Usuario(SQLModel, table=True):
    """Persona que utiliza el sistema LPA."""

    __tablename__ = "usuario"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=150)
    correo: str = Field(max_length=255, unique=True, index=True)
    contrasena_hash: str = Field(max_length=255)
    activo: bool = Field(default=True)
    rol_id: int = Field(foreign_key="rol.id")

    rol: "Rol" = Relationship(back_populates="usuarios")
    areas: list["Area"] = Relationship(
        back_populates="usuarios",
        link_model=UsuarioArea,
    )
    celulas: list["Celula"] = Relationship(
        back_populates="usuarios",
        link_model=UsuarioCelula,
    )
    ejecuciones_auditoria: list["EjecucionAuditoria"] = Relationship(
        back_populates="usuario",
    )
    hallazgos_responsables: list["Hallazgo"] = Relationship(
        back_populates="responsables",
        link_model=HallazgoResponsable,
    )

    @property
    def rol_nombre(self) -> str:
        """Nombre del rol asociado al usuario."""
        return self.rol.nombre if self.rol else ""
```

### `auditoria` — `backend/app/models/auditoria.py`

```python
class Auditoria(SQLModel, table=True):
    """Auditoria disponible dentro del sistema."""

    __tablename__ = "auditoria"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=150, index=True)
    descripcion: str | None = Field(default=None, max_length=500)
    activa: bool = Field(default=True)
    tipo_respuesta: str = Field(default="semaforo", max_length=20)
    dia_semana: int | None = Field(default=None, ge=0, le=6)
    programacion_semanal: bool = Field(default=False)
    capa_id: int = Field(foreign_key="capa.id")
    frecuencia_id: int = Field(foreign_key="frecuencia.id")
    area_id: int | None = Field(default=None, foreign_key="area.id")

    capa: "Capa" = Relationship(back_populates="auditorias")
    frecuencia: "Frecuencia" = Relationship(back_populates="auditorias")
    area: Optional["Area"] = Relationship(back_populates="auditorias")
    criterios: list["Criterio"] = Relationship(back_populates="auditoria")
    ejecuciones_auditoria: list["EjecucionAuditoria"] = Relationship(
        back_populates="auditoria",
    )
    dias_rows: list["AuditoriaDia"] = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "cascade": "all, delete-orphan",
        },
    )
```

### `auditoria_dia` — `backend/app/models/auditoria_dia.py`

```python
class AuditoriaDia(SQLModel, table=True):
    """Día hábil (0=Lunes..4=Viernes) en que una auditoría se ejecuta."""

    __tablename__ = "auditoria_dia"
    __table_args__ = (
        UniqueConstraint("auditoria_id", "dia_semana", name="uq_auditoria_dia"),
    )

    id: int | None = Field(default=None, primary_key=True)
    auditoria_id: int = Field(foreign_key="auditoria.id", index=True)
    dia_semana: int = Field(ge=0, le=4)
```

### `programacion_semanal` — `backend/app/models/programacion_semanal.py`

```python
class ProgramacionSemanal(SQLModel, table=True):
    """Asigna, por semana, una auditoría a cada día hábil."""

    __tablename__ = "programacion_semanal"

    id: int | None = Field(default=None, primary_key=True)
    semana_inicio: date = Field(index=True)  # lunes de la semana
    dia_semana: int = Field(ge=0, le=4)
    auditoria_id: int = Field(foreign_key="auditoria.id")
```

### `celula` — `backend/app/models/celula.py`

```python
class Celula(SQLModel, table=True):
    """Linea o celula de produccion dentro de un area."""

    __tablename__ = "celula"
    __table_args__ = (UniqueConstraint("area_id", "numero"),)

    id: int | None = Field(default=None, primary_key=True)
    numero: int
    activa: bool = Field(default=True)
    area_id: int = Field(foreign_key="area.id")

    area: "Area" = Relationship(back_populates="celulas")
    ejecuciones_auditoria: list["EjecucionAuditoria"] = Relationship(
        back_populates="celula",
    )
    usuarios: list["Usuario"] = Relationship(
        back_populates="celulas",
        link_model=UsuarioCelula,
    )
```

### `criterio` — `backend/app/models/criterio.py`

```python
class Criterio(SQLModel, table=True):
    """Punto de inspeccion dentro de una auditoria."""

    __tablename__ = "criterio"

    id: int | None = Field(default=None, primary_key=True)
    descripcion: str = Field(max_length=500)
    orden: int = Field(default=1, ge=1)
    activo: bool = Field(default=True)
    auditoria_id: int = Field(foreign_key="auditoria.id")

    # Jerarquia opcional para agrupar criterios bajo titulos/subtitulos
    seccion: str | None = Field(default=None, max_length=150)
    subseccion: str | None = Field(default=None, max_length=150)
    subtitulo: str | None = Field(default=None, max_length=150)

    auditoria: "Auditoria" = Relationship(back_populates="criterios")
    respuestas: list["Respuesta"] = Relationship(back_populates="criterio")
```

### `ejecucion_auditoria` — `backend/app/models/ejecucion_auditoria.py`

```python
class EjecucionAuditoria(SQLModel, table=True):
    """Auditoria realizada por un usuario en una fecha determinada."""

    __tablename__ = "ejecucion_auditoria"

    id: int | None = Field(default=None, primary_key=True)
    fecha: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    fecha_programada: datetime | None = Field(default=None)
    observaciones: str | None = Field(default=None, max_length=1000)
    estado: str = Field(default="en_proceso", max_length=20)
    auditoria_id: int = Field(foreign_key="auditoria.id")
    usuario_id: int = Field(foreign_key="usuario.id")
    celula_id: int | None = Field(default=None, foreign_key="celula.id")

    auditoria: "Auditoria" = Relationship(back_populates="ejecuciones_auditoria")
    usuario: "Usuario" = Relationship(back_populates="ejecuciones_auditoria")
    celula: Optional["Celula"] = Relationship(back_populates="ejecuciones_auditoria")
    respuestas: list["Respuesta"] = Relationship(back_populates="ejecucion_auditoria")
```

### `respuesta` — `backend/app/models/respuesta.py`

```python
class Respuesta(SQLModel, table=True):
    """Resultado observado para un criterio durante una ejecucion."""

    __tablename__ = "respuesta"
    __table_args__ = (
        UniqueConstraint(
            "ejecucion_auditoria_id",
            "criterio_id",
            name="uq_respuesta_ejecucion_criterio",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    valor: str = Field(max_length=20)
    observaciones: str | None = Field(default=None, max_length=1000)
    ejecucion_auditoria_id: int = Field(foreign_key="ejecucion_auditoria.id")
    criterio_id: int = Field(foreign_key="criterio.id")

    ejecucion_auditoria: "EjecucionAuditoria" = Relationship(back_populates="respuestas")
    criterio: "Criterio" = Relationship(back_populates="respuestas")
    hallazgo: Optional["Hallazgo"] = Relationship(
        back_populates="respuesta",
        sa_relationship_kwargs={"uselist": False},
    )
```

### `hallazgo` — `backend/app/models/hallazgo.py`

```python
ESTADOS_HALLAZGO = ("abierto", "en_correccion", "cierre_solicitado", "cerrado")


class Hallazgo(SQLModel, table=True):
    """Desviacion detectada durante una auditoria (ticket de correccion)."""

    __tablename__ = "hallazgo"

    id: int | None = Field(default=None, primary_key=True)
    descripcion: str = Field(max_length=1000)
    fecha_creacion: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    respuesta_id: int = Field(foreign_key="respuesta.id", unique=True)

    estado: str = Field(default="abierto", max_length=20)
    accion_correctiva: str | None = Field(default=None, max_length=1000)
    area_responsable_id: int | None = Field(
        default=None, foreign_key="area.id"
    )
    fecha_limite: datetime | None = Field(default=None)
    fecha_cierre: datetime | None = Field(default=None)

    respuesta: "Respuesta" = Relationship(back_populates="hallazgo")
    evidencias: list["Evidencia"] = Relationship(back_populates="hallazgo")
    responsables: list["Usuario"] = Relationship(
        back_populates="hallazgos_responsables",
        link_model=HallazgoResponsable,
    )
    area_responsable: Optional["Area"] = Relationship()
    seguimientos: list["HallazgoSeguimiento"] = Relationship(
        back_populates="hallazgo",
    )
```

### `evidencia` — `backend/app/models/evidencia.py`

```python
class Evidencia(SQLModel, table=True):
    """Archivo asociado a un hallazgo."""

    __tablename__ = "evidencia"

    id: int | None = Field(default=None, primary_key=True)
    ruta_archivo: str = Field(max_length=500)
    tipo_archivo: str = Field(default="fotografia", max_length=100)
    tipo: str = Field(default="original", max_length=20)
    fecha_carga: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    hallazgo_id: int = Field(foreign_key="hallazgo.id")

    hallazgo: "Hallazgo" = Relationship(back_populates="evidencias")
```

### `hallazgo_seguimiento` — `backend/app/models/hallazgo_seguimiento.py`

```python
class HallazgoSeguimiento(SQLModel, table=True):
    """Entrada del historial de un hallazgo (ticket)."""

    __tablename__ = "hallazgo_seguimiento"

    id: int | None = Field(default=None, primary_key=True)
    hallazgo_id: int = Field(foreign_key="hallazgo.id", index=True)
    usuario_id: int = Field(foreign_key="usuario.id")
    tipo: str = Field(max_length=30)
    detalle: str | None = Field(default=None, max_length=1000)
    estado_desde: str | None = Field(default=None, max_length=20)
    estado_hasta: str | None = Field(default=None, max_length=20)
    fecha_creacion: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    hallazgo: "Hallazgo" = Relationship(back_populates="seguimientos")
    usuario: "Usuario" = Relationship()
```

### `usuario_area` — `backend/app/models/usuario_area.py`

```python
class UsuarioArea(SQLModel, table=True):
    """Asigna usuarios a las areas donde pueden operar."""

    __tablename__ = "usuario_area"

    usuario_id: int = Field(foreign_key="usuario.id", primary_key=True)
    area_id: int = Field(foreign_key="area.id", primary_key=True)
```

### `usuario_celula` — `backend/app/models/usuario_celula.py`

```python
class UsuarioCelula(SQLModel, table=True):
    """Asigna usuarios a las células donde pueden operar (N:M)."""

    __tablename__ = "usuario_celula"

    usuario_id: int = Field(foreign_key="usuario.id", primary_key=True)
    celula_id: int = Field(foreign_key="celula.id", primary_key=True)
```

### `usuario_supervisor` — `backend/app/models/usuario_supervisor.py`

```python
class UsuarioSupervisor(SQLModel, table=True):
    """Relaciona a un Gerente con los Supervisores a su cargo (N:M)."""

    __tablename__ = "usuario_supervisor"

    gerente_id: int = Field(foreign_key="usuario.id", primary_key=True)
    supervisor_id: int = Field(foreign_key="usuario.id", primary_key=True)
```

### `hallazgo_responsable` — `backend/app/models/hallazgo_responsable.py`

```python
class HallazgoResponsable(SQLModel, table=True):
    """Relaciona hallazgos con los usuarios responsables de atenderlos."""

    __tablename__ = "hallazgo_responsable"

    hallazgo_id: int = Field(foreign_key="hallazgo.id", primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", primary_key=True)
```

---

## Historial de migraciones (Alembic)

| Revisión | Descripción |
| --- | --- |
| `43e68b1dc730` | `initial_schema` (creación de todas las tablas). |
| `77d7424ea64a` | `celula` reemplaza `nombre` y `descripcion` por `numero`. |
| `9c2f1a4b7d01` | `criterio` agrega jerarquía `seccion`/`subseccion`/`subtitulo`. |
| `b1d4e7f20a35` | `hallazgo` agrega seguimiento (`estado`, `accion_correctiva`, `area_responsable_id`, `fecha_cierre`). |
| `e5f8a1b2c3d4` | `auditoria` agrega `tipo_respuesta` (`semaforo` o `cumplimiento`). |
| `a6b7c8d9e0f1` | Programación: `frecuencia.dias`, `ejecucion_auditoria.fecha_programada`, tabla `usuario_celula`. |
| `b1c2d3e4f5a6` | Asignación por rol: tabla `usuario_supervisor` (gerente ↔ supervisores). |
| `c2d3e4f5a6b7` | Semanal: `capa.requiere_celula`, `auditoria.dia_semana`. |
| `d3e4f5a6b7c8` | Tickets: `hallazgo.fecha_limite`, tabla `hallazgo_seguimiento`, `evidencia.tipo` (`original`/`correccion`) y renombrado de estado `en_proceso` → `en_correccion`. |
| `e4f5a6b7c8d9` | Programación semanal: `auditoria.programacion_semanal`, tabla `programacion_semanal`. |
| `f1a2b3c4d5e6` | Días hábiles elegidos: tabla `auditoria_dia`. |

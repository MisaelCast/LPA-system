# Esquema de Base de Datos

## Objetivo

Este documento describe el diseño físico de la base de datos del Sistema LPA: las tablas, columnas, restricciones y relaciones tal como existen tras aplicar todas las migraciones de Alembic.

Complementa a [Modelo de Dominio](./01-domain-model.md), que describe el negocio y no el diseño de la base de datos.

| Dato | Valor |
| --- | --- |
| Motor | PostgreSQL |
| ORM | SQLModel (SQLAlchemy + Pydantic) |
| Modelos | `backend/app/models/` |
| Migraciones | `backend/migrations/versions/` |

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
| 7 | `celula` | Línea o célula de producción dentro de un área. |
| 8 | `criterio` | Punto de inspección dentro de una auditoría. |
| 9 | `ejecucion_auditoria` | Auditoría realizada por un usuario en una fecha. |
| 10 | `respuesta` | Resultado observado para un criterio durante una ejecución. |
| 11 | `hallazgo` | Desviación detectada durante una auditoría. |
| 12 | `evidencia` | Archivo asociado a un hallazgo. |
| 13 | `usuario_area` | Tabla intermedia N:M entre usuario y área. |
| 14 | `hallazgo_responsable` | Tabla intermedia N:M entre hallazgo y usuario. |

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
    id           SERIAL       PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL,
    descripcion  VARCHAR(255),
    activa       BOOLEAN      NOT NULL DEFAULT TRUE
);
CREATE UNIQUE INDEX ix_capa_nombre ON capa (nombre);

-- frecuencia: Periodicidad con la que debe ejecutarse una auditoría.
CREATE TABLE frecuencia (
    id           SERIAL       PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL,
    descripcion  VARCHAR(255)
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
    capa_id       INTEGER      NOT NULL REFERENCES capa (id),
    frecuencia_id INTEGER      NOT NULL REFERENCES frecuencia (id),
    area_id       INTEGER      REFERENCES area (id)
);
CREATE INDEX ix_auditoria_nombre ON auditoria (nombre);

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
    id            SERIAL        PRIMARY KEY,
    fecha         TIMESTAMP     NOT NULL,
    observaciones VARCHAR(1000),
    estado        VARCHAR(20)   NOT NULL DEFAULT 'en_proceso',
    auditoria_id  INTEGER       NOT NULL REFERENCES auditoria (id),
    usuario_id    INTEGER       NOT NULL REFERENCES usuario (id),
    celula_id     INTEGER       REFERENCES celula (id)
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

-- hallazgo: Desviación detectada durante una auditoría.
CREATE TABLE hallazgo (
    id                  SERIAL        PRIMARY KEY,
    descripcion         VARCHAR(1000) NOT NULL,
    fecha_creacion      TIMESTAMP     NOT NULL,
    respuesta_id        INTEGER       NOT NULL REFERENCES respuesta (id),
    estado              VARCHAR(20)   NOT NULL DEFAULT 'abierto',
    accion_correctiva   VARCHAR(1000),
    area_responsable_id INTEGER       REFERENCES area (id),
    fecha_cierre        TIMESTAMP WITH TIME ZONE,
    CONSTRAINT hallazgo_respuesta_id_key UNIQUE (respuesta_id)
);

-- evidencia: Archivo asociado a un hallazgo.
CREATE TABLE evidencia (
    id           SERIAL       PRIMARY KEY,
    ruta_archivo VARCHAR(500) NOT NULL,
    tipo_archivo VARCHAR(100) NOT NULL DEFAULT 'fotografia',
    fecha_carga  TIMESTAMP    NOT NULL,
    hallazgo_id  INTEGER      NOT NULL REFERENCES hallazgo (id)
);

-- usuario_area: Asigna usuarios a las áreas donde pueden operar (N:M).
CREATE TABLE usuario_area (
    usuario_id INTEGER NOT NULL REFERENCES usuario (id),
    area_id    INTEGER NOT NULL REFERENCES area (id),
    PRIMARY KEY (usuario_id, area_id)
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
capa                 1 --- N  auditoria
frecuencia           1 --- N  auditoria
auditoria            1 --- N  criterio
auditoria            1 --- N  ejecucion_auditoria
celula               1 --- N  ejecucion_auditoria
usuario              1 --- N  ejecucion_auditoria
ejecucion_auditoria  1 --- N  respuesta
criterio             1 --- N  respuesta
respuesta            1 --- 1  hallazgo
hallazgo             1 --- N  evidencia
hallazgo             N --- N  usuario              (via hallazgo_responsable)
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
ESTADOS_HALLAZGO = ("abierto", "en_proceso", "cerrado")


class Hallazgo(SQLModel, table=True):
    """Desviacion detectada durante una auditoria."""

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
    fecha_cierre: datetime | None = Field(default=None)

    respuesta: "Respuesta" = Relationship(back_populates="hallazgo")
    evidencias: list["Evidencia"] = Relationship(back_populates="hallazgo")
    responsables: list["Usuario"] = Relationship(
        back_populates="hallazgos_responsables",
        link_model=HallazgoResponsable,
    )
    area_responsable: Optional["Area"] = Relationship()
```

### `evidencia` — `backend/app/models/evidencia.py`

```python
class Evidencia(SQLModel, table=True):
    """Archivo asociado a un hallazgo."""

    __tablename__ = "evidencia"

    id: int | None = Field(default=None, primary_key=True)
    ruta_archivo: str = Field(max_length=500)
    tipo_archivo: str = Field(default="fotografia", max_length=100)
    fecha_carga: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    hallazgo_id: int = Field(foreign_key="hallazgo.id")

    hallazgo: "Hallazgo" = Relationship(back_populates="evidencias")
```

### `usuario_area` — `backend/app/models/usuario_area.py`

```python
class UsuarioArea(SQLModel, table=True):
    """Asigna usuarios a las areas donde pueden operar."""

    __tablename__ = "usuario_area"

    usuario_id: int = Field(foreign_key="usuario.id", primary_key=True)
    area_id: int = Field(foreign_key="area.id", primary_key=True)
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

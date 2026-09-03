# LPA System

Sistema web para la gestión y ejecución de auditorías de procesos LPA (Layer Process Audit). Permite definir auditorías con sus criterios de evaluación, ejecutarlas en las distintas capas del proceso (Auditor, Supervisor, Gerente) y registrar hallazgos con evidencia.

## Stack tecnológico

| Capa       | Tecnología                                   |
| ---------- | -------------------------------------------- |
| Backend    | Python, FastAPI, SQLModel, PostgreSQL, Alembic |
| Frontend   | Vue 3, TypeScript, Vite, Pinia, Vue Router   |
| Autenticación | JWT, bcrypt                               |

## Funcionalidades principales

- Autenticación con roles (Administrador, Supervisor, Auditor) y rutas protegidas.
- Gestión de usuarios, áreas, células, capas, frecuencias y auditorías.
- Definición de criterios por auditoría.
- Ejecución de auditorías con respuestas (verde, amarillo, rojo, no aplica).
- Registro de hallazgos con responsables.
- Historial de auditorías realizadas.

## Estructura del proyecto

```
lpa-system/
├── backend/     # API FastAPI + base de datos
│   ├── app/     # config, auth, modelos, repositorios, servicios, API
│   ├── migrations/  # migraciones de Alembic
│   └── tests/   # pruebas del backend
├── frontend/    # aplicación Vue 3 + TypeScript
│   └── src/     # vistas, layouts, stores, servicios, tipos
├── database/    # recursos de base de datos
└── docs/        # documentación (modelo de dominio)
```

## Requisitos

- Python 3.13+
- Node.js 22+ / 24+
- PostgreSQL

## Backend

### Configuración

```bash
cd backend
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edita `.env` con los datos de tu base de datos:

```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=lpa_system
DATABASE_USER=postgres
DATABASE_PASSWORD=tu_contraseña
SECRET_KEY="tu_secret_key_de_al_menos_32_caracteres"
BACKEND_CORS_ORIGINS=http://localhost:5173
```

### Base de datos

```bash
createdb -U postgres lpa_system
alembic upgrade head
```

El esquema se administra con Alembic. Los datos mínimos (roles, capas, usuario administrador, frecuencias, áreas y una auditoría de ejemplo) se siembran automáticamente al iniciar la API.

### Ejecutar

```bash
uvicorn app.main:app --reload
```

La API queda disponible en `http://127.0.0.1:8000` y su documentación interactiva en `/docs`.

### Pruebas

```bash
cd backend
pytest
```

## Frontend

### Configuración

```bash
cd frontend
npm install
```

Crea el archivo `.env` si no existe:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### Ejecutar

```bash
npm run dev
```

La aplicación queda disponible en `http://localhost:5173`.

### Scripts útiles

```bash
npm run build       # compilar para producción
npm run type-check  # verificación de tipos
npm run lint        # ESLint
npm run test        # Vitest
```

## Credenciales por defecto

El seed inicial crea el usuario administrador:

- **Correo:** `admin@lpa.com`
- **Contraseña:** la definida en `DEFAULT_ADMIN_PASSWORD` de `.env` (por defecto `Admin123*`).

## Documentación

- `docs/01-domain-model.md`: modelo de dominio del sistema.

## Licencia

MIT. Ver [LICENSE](LICENSE).
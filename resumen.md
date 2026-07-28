# Resumen de Implementaciones

## feat: configurar arquitectura base del frontend

**Commit:** e8f2cac

### Carpetas creadas
```
src/api/
src/assets/
src/components/
src/components/common/
src/components/layout/
src/components/ui/
src/layouts/
src/services/
src/stores/
src/types/
src/utils/
src/views/
src/views/auth/
src/views/dashboard/
src/views/usuarios/
```

### Archivos creados
- `src/views/auth/LoginView.vue`
- `src/views/dashboard/DashboardView.vue`
- `src/views/usuarios/UsuariosView.vue`
- `src/layouts/MainLayout.vue`

### Archivos modificados
- `src/App.vue` → `<RouterView />`
- `src/router/index.ts` → rutas `/login`, `/dashboard`, `/usuarios`

### Dependencias instaladas
- `eslint-plugin-oxlint` (faltante del scaffold)

### Validaciones
- `npm run lint` → sin errores
- `npm run dev` → Vite arranca correctamente

---

## feat: configurar cliente HTTP con Axios

**Commit:** 71f353a

### Archivos creados
- `.env` → `VITE_API_BASE_URL=http://localhost:8000`
- `src/api/api.ts` → instancia Axios centralizada con interceptores
- `src/types/auth.ts` → tipos `Token`, `CredencialesLogin`, `Usuario`

### Archivos modificados
- `env.d.ts` → tipado de `ImportMetaEnv` para `VITE_API_BASE_URL`

### Dependencias instaladas
- `axios`

### Cliente HTTP (`src/api/api.ts`)
- `baseURL` desde variable de entorno `VITE_API_BASE_URL`
- **Request interceptor**: agrega `Authorization: Bearer <token>` desde `localStorage`
- **Response interceptor**: captura 401 y loguea advertencia (sin redirección todavía)

### Validaciones
- `npm run lint` → sin errores
- `npm run dev` → Vite arranca correctamente

---

## feat: implementar store de autenticación

**Commit:** 3d9b50b

### Archivos creados
- `src/stores/auth.ts` → store Pinia de autenticación

### Archivos modificados
Ninguno.

### Estado
- `token: string | null` — inicializado desde `localStorage`

### Getters
- `isAuthenticated` — `true` si existe token, `false` en caso contrario

### Acciones
- `setToken(value)` — actualiza el estado y persiste en `localStorage`
- `clearToken()` — limpia el estado y elimina de `localStorage`

### Validaciones
- `npm run lint` → sin errores
- `npm run dev` → Vite arranca correctamente

---

## feat: implementar servicio de autenticación

**Commit:** a1ffa7c

### Archivos creados
- `src/services/auth.service.ts` → funciones `login()` y `logout()`

### Archivos modificados
Ninguno.

### Funciones
- `login(credentials)` → `POST /auth/login` vía Axios, retorna `Token`
- `logout()` → placeholder vacío

### Validaciones
- `npm run lint` → sin errores
- `npm run dev` → Vite arranca correctamente

---

## feat: implementar inicio de sesión

**Commit:** fed27c3

### Archivos modificados
- `src/views/auth/LoginView.vue` → formulario de login funcional

### Flujo
1. Formulario con correo, contraseña y botón "Iniciar sesión"
2. Al submit → `auth.service.login()` → `POST /auth/login`
3. Éxito → `authStore.setToken()` + redirección a `/dashboard`
4. Error 401 → "Correo o contraseña incorrectos."
5. Error 403 → mensaje del backend
6. Error de red → "No se pudo conectar con el servidor."
7. Botón deshabilitado durante carga

### Validaciones
- `npm run lint` → sin errores
- `npm run dev` → Vite arranca correctamente

---

## feat: proteger rutas mediante autenticación

**Commit:** 2aa96b5

### Archivos modificados
- `src/router/index.ts` → Navigation Guard global

### Flujo
- `meta.requiresAuth === true` + no autenticado → redirect a `/login`
- Ruta `/login` + autenticado → redirect a `/dashboard`
- `/dashboard` y `/usuarios` protegidas, `/login` pública

### Validaciones
- `npm run lint` → sin errores
- `npm run dev` → Vite arranca correctamente

---

## feat: implementar layout principal

**Commit:** pendiente

### Archivos modificados
- `src/layouts/MainLayout.vue` → sidebar + header + contenido
- `src/router/index.ts` → rutas hijas bajo MainLayout

### Estructura
- **Sidebar**: navegación con `RouterLink` (Dashboard, Usuarios)
- **Header**: "LPA System" + "Administrador" (fijo)
- **Contenido**: `<RouterView />` para las vistas hijas
- `/login` fuera del layout, `/dashboard` y `/usuarios` dentro

### Validaciones
- `npm run lint` → sin errores
- `npm run dev` → Vite arranca correctamente

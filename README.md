# AgroConecta — Backend

API REST para la plataforma de comercialización agrícola directa para pequeños productores del departamento de La Guajira, Colombia.

---

## Descripción general

AgroConecta conecta productores agrícolas con compradores eliminando intermediarios. Los productores publican sus productos, los compradores los encuentran en el catálogo y negocian mediante un chat asíncrono. El productor formaliza el acuerdo creando un pedido.

**Repositorio frontend:** [agroconecta_frontend](https://github.com/DiegoDeluque1504/agroconecta_frontend)

---

## 🚀 Refactorización de Seguridad y Funcional (Junio 2026)

- **Reconocimiento de Dispositivo:** Se registra la IP, User-Agent, navegador y sistema operativo de cada inicio de sesión. Si el dispositivo es nuevo, se envía una alerta por correo a través de Resend.
- **Validación de CAPTCHA (Cloudflare Turnstile):** Implementación de verificación en el backend de tokens de Turnstile para evitar registros y logins automatizados.
- **Validación Estricta de Contraseñas:** Se exige que la contraseña contenga un mínimo de 8 caracteres, al menos una letra y al menos un número (tanto en backend como en frontend).
- **Flujo Simplificado de Verificación:** Al registrarse, el usuario recibe un correo con un enlace de verificación directa. Al hacer clic, se activa la cuenta y se le redirige directamente al login sin ingresar códigos manuales.
- **Rediseño del Flujo de Negociación:** La creación de un pedido ya no cierra la conversación. El chat permanece disponible en el estado `pedido_creado` para coordinar la entrega. Solo se finaliza o cancela al entregar o cancelar el pedido.
- **Cancelación Mutua de Pedidos:** Tanto productores como compradores pueden cancelar un pedido indicando un motivo obligatorio, el cual queda registrado (`cancelado_por`, `motivo_cancelacion`, `fecha_cancelacion`) y se muestra en la interfaz.
- **Recordatorio de Mensajes No Leídos:** Un comando en segundo plano busca mensajes no leídos con más de 10 minutos y envía un correo consolidado por destinatario para notificar sobre los mensajes pendientes.

---

## Integrantes

| Nombre | Rol |
|---|---|
| Diego De Luque | Desarrollador principal / Backend |
| Carlos Basilio | Desarrollador / Backend |
| David Royero | Desarrollador / Frontend |
| Daniel Royero | Desarrollador / Frontend |

**Institución:** Universidad de La Guajira  
**Programa:** Ingeniería de Sistemas  
**Asignatura:** Formulación y Evaluación de Proyectos (Cód. 273271)

---

## Stack tecnológico

| Tecnología | Versión / uso |
|---|---|
| Python | 3.10+ |
| Django | 6.x |
| Django REST Framework | 3.17+ |
| PostgreSQL | 15 |
| Docker | Contenedor de base de datos |
| WSL 2 (Ubuntu) | Entorno de desarrollo |
| JWT (SimpleJWT) | Autenticación |
| django-axes | Bloqueo por intentos fallidos de login |
| django-cors-headers | CORS para el frontend Angular |
| Cloudinary | Imágenes y audios |
| python-dotenv | Variables de entorno |
| Resend (API HTTP) | Correos de verificación |
| Render | Despliegue en producción |
| Gunicorn | Servidor WSGI en Render |

---

## Arquitectura del proyecto

```
agroconectabackend/
├── config/
│   ├── settings.py          # Configuración general
│   ├── urls.py              # URLs principales
│   ├── throttling.py        # Rate limiting (invitados y autenticados)
│   ├── exceptions.py        # Respuestas de error personalizadas
│   └── wsgi.py
├── usuarios/
│   ├── models.py            # Usuario, Municipio, TokenVerificacion
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── email_service.py     # Envío de correos vía API Resend
│   ├── lockout_utils.py     # Respuestas JSON de django-axes
│   ├── fixtures/municipios.json
│   └── management/commands/clean_expired_tokens.py
├── docs/
│   └── EMAIL_RESEND.md      # Dominio y correo en producción
├── productos/
├── negociacion/
├── pedidos/
├── notificaciones/
├── file_validators.py       # Validación de fotos (5 MB) y audios (10 MB)
├── manage.py
└── requirements.txt
```

---

## Modelos y estados clave

### Negociación

| Estado | Descripción |
|---|---|
| `abierta` | En curso; acepta mensajes y permite crear propuesta de pedido |
| `pedido_creado` | Se ha creado la propuesta de pedido. El chat sigue abierto para coordinar la entrega |
| `finalizada` | El pedido ha sido entregado con éxito; ya no se aceptan nuevos mensajes |
| `cancelada` | La negociación o el pedido fue cancelada por alguna de las partes |

> El pedido solo se crea desde una negociación en estado `abierta`. Al crearse el pedido, la negociación pasa a `pedido_creado` manteniendo la comunicación activa.

### Pedido

`pendiente` (esperando confirmación del comprador) → `confirmado` → `preparacion` → `en_camino` → `entregado` (o `cancelado` en cualquier momento).

---

## Seguridad

### Rate limiting

| Tipo de usuario | Límite | HTTP | Código de error |
|---|---|---|---|
| Visitante anónimo (exploración) | 100 peticiones/día por IP | 403 | `guest_exploration_limit` |
| Usuario autenticado | 3000 peticiones/día | 429 | `api_rate_limit` |

Rutas **exentas** del límite de invitado: `registro`, `login`, `verificar-email`, `token/refresh`, `municipios`.

El límite de invitado activa **modo restringido** en el frontend (conversión a registro/login), no bloqueo permanente de IP.

### django-axes (login)

- Bloqueo tras **5 intentos fallidos** durante **1 hora**
- Respuesta **429** con JSON:

```json
{
  "code": "axes_lockout",
  "detail": "Demasiados intentos fallidos. Tu acceso ha sido bloqueado temporalmente...",
  "cooloff_seconds": 3600
}
```

**Limpiar bloqueos en desarrollo:**

```bash
python manage.py axes_reset_ip 127.0.0.1
python manage.py axes_reset_username usuario@email.com
python manage.py axes_reset   # todos (solo dev)
```

### Validación GPS (perfil productor)

Coordenadas válidas dentro del bounding box de **La Guajira** (`usuarios/serializers.py`).

### Validación de archivos (`file_validators.py`)

| Tipo | Formatos | Tamaño máximo |
|---|---|---|
| Fotos de producto | JPG, PNG, WebP | 5 MB |
| Audios en chat | MP3, WAV, OGG, WebM | 10 MB |

### Headers HTTP

- `X_FRAME_OPTIONS = DENY`
- `SECURE_BROWSER_XSS_FILTER = True`
- `SECURE_CONTENT_TYPE_NOSNIFF = True`

### Anti-registro masivo

Si un correo ya tiene cuenta sin verificar y un token vigente, responde **400**:

```json
{
  "code": "token_activo",
  "error": "Ya existe una solicitud de registro pendiente para este correo..."
}
```

### Limpieza de tokens expirados

```bash
python manage.py clean_expired_tokens --dry-run
python manage.py clean_expired_tokens
```

### Recordatorio de mensajes no leídos

Busca mensajes que no hayan sido leídos por más de 10 minutos y envía un correo consolidado de recordatorio usando la API de Resend:

```bash
python manage.py enviar_recordatorios
```

---

## Instalación local

### Requisitos

- WSL 2 (Ubuntu), Docker, Python 3.10+, Git

### 1. PostgreSQL en Docker

```bash
sudo service docker start

docker run --name agroconecta_db \
  -e POSTGRES_USER=agroconecta_user \
  -e POSTGRES_PASSWORD=agroconecta2026 \
  -e POSTGRES_DB=agroconecta_db \
  -p 5432:5432 \
  -v agroconecta_pgdata:/var/lib/postgresql/data \
  --restart unless-stopped \
  -d postgres:15
```

### 2. Clonar e instalar

```bash
git clone https://github.com/DiegoDeluque1504/agroconecta_backend.git
cd agroconecta_backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Archivo `.env` (raíz del proyecto)

Copia `.env.example` y completa los valores:

```
SECRET_KEY=tu-clave-secreta
DEBUG=True
DB_NAME=agroconecta_db
DB_USER=agroconecta_user
DB_PASSWORD=agroconecta2026
DB_HOST=localhost
DB_PORT=5432
CLOUDINARY_CLOUD_NAME=tu_cloud_name
CLOUDINARY_API_KEY=tu_api_key
CLOUDINARY_API_SECRET=tu_api_secret
RESEND_API_KEY=re_xxxxxxxx
FRONTEND_URL=http://localhost:4200
```

> El `.env` no debe subirse a GitHub (está en `.gitignore`).

### 4. Migraciones y datos iniciales

```bash
python manage.py migrate
python manage.py loaddata usuarios/fixtures/municipios.json
python manage.py loaddata productos/fixtures/categorias.json
```

### 5. Servidor

```bash
python manage.py runserver
```

API disponible en `http://127.0.0.1:8000/api/v1/`

### Comandos del día a día

```bash
sudo service docker start && docker start agroconecta_db
cd ~/agroconectabackend && source venv/bin/activate && python manage.py runserver
```

---

## Endpoints de la API

Base URL: `http://127.0.0.1:8000/api/v1/`

### Usuarios

| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| POST | `usuarios/registro/` | Registrar usuario | No |
| POST | `usuarios/verificar-email/` | Activar cuenta con token | No |
| POST | `usuarios/login/` | Iniciar sesión (JWT) | No |
| POST | `usuarios/token/refresh/` | Renovar access token | No |
| GET/PUT | `usuarios/perfil/` | Ver y editar perfil | Sí |
| POST | `usuarios/cambiar-password/` | Cambiar contraseña | Sí |
| GET | `usuarios/municipios/` | Municipios de La Guajira | No |

**Cambiar contraseña** — body:

```json
{
  "password_actual": "...",
  "password_nueva": "..."
}
```

### Productos

| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| GET | `productos/categorias/` | Categorías | No |
| GET | `productos/catalogo/` | Catálogo paginado (12/página) | No |
| GET | `productos/<id>/` | Detalle | No |
| POST | `productos/crear/` | Publicar producto | Productor |
| PUT/PATCH | `productos/<id>/gestionar/` | Editar producto | Dueño |
| DELETE | `productos/<id>/gestionar/` | Eliminar producto | Dueño |
| POST | `productos/<id>/fotos/agregar/` | Agregar foto | Dueño |
| DELETE | `productos/fotos/<id>/eliminar/` | Eliminar foto | Dueño |
| GET | `productos/mis-productos/` | Mis productos | Productor |

**Filtros del catálogo:** `categoria`, `municipio`, `precio_min`, `precio_max`, `busqueda`, `page`.

### Negociaciones

| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| POST | `negociaciones/iniciar/<producto_id>/` | Iniciar negociación | Sí |
| GET | `negociaciones/mis-negociaciones/` | Listar | Sí |
| GET | `negociaciones/<id>/` | Detalle + mensajes | Sí |
| POST | `negociaciones/<id>/mensajes/` | Enviar texto o audio | Sí |
| POST | `negociaciones/<id>/estado/` | Cerrar sin acuerdo / cancelar | Sí |

### Pedidos

| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| POST | `pedidos/crear/<negociacion_id>/` | Crear pedido (negociación abierta) | Productor |
| GET | `pedidos/mis-pedidos/` | Listar pedidos | Sí |
| GET | `pedidos/<id>/` | Detalle + historial | Sí |
| POST | `pedidos/<id>/estado/` | Actualizar estado | Productor |
| POST | `pedidos/<id>/calificar/` | Calificar tras entrega | Sí |

### Notificaciones

| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| GET | `notificaciones/` | Listar | Sí |
| GET | `notificaciones/no-leidas/` | Conteo | Sí |
| POST | `notificaciones/<id>/leer/` | Marcar leída | Sí |
| POST | `notificaciones/leer-todas/` | Marcar todas | Sí |

---

## Flujos principales

### Registro y autenticación

```
POST /usuarios/registro/        → cuenta inactiva + correo con enlace de verificación
POST /usuarios/verificar-email/ → cuenta activa + JWT
POST /usuarios/login/           → JWT (access 1 h, refresh 7 días)
```

El registro envía un enlace a `{FRONTEND_URL}/auth/verificar-email?token=...`. En desarrollo sin `RESEND_API_KEY` el enlace se imprime en consola.

### Compra completa

```
GET  /productos/catalogo/
POST /negociaciones/iniciar/<id>/
POST /negociaciones/<id>/mensajes/
POST /pedidos/crear/<negociacion_id>/   (solo si abierta)
POST /pedidos/<id>/estado/
POST /pedidos/<id>/calificar/
```

### Autenticación en peticiones protegidas

```
Authorization: Bearer <access_token>
```

---

## Producción

### URLs desplegadas

| Recurso | URL |
|---------|-----|
| API | https://agroconecta-backend-sjmy.onrender.com/api/v1 |
| Frontend (CORS) | https://agroconecta-frontend-sigma.vercel.app |

### Render

- **Comando de inicio:** `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
- **Base de datos:** PostgreSQL (variables de entorno de Render)
- **Rama:** `main`

### Variables de entorno (Render)

| Variable | Descripción |
|----------|-------------|
| `SECRET_KEY` | Clave Django |
| `DEBUG` | `False` |
| `RESEND_API_KEY` | API key de Resend |
| `RESEND_FROM_EMAIL` | Remitente con dominio verificado (ej. `AgroConecta <noreply@tudominio.com>`) |
| `FRONTEND_URL` | URL del frontend en Vercel |
| `CLOUDINARY_*` | Credenciales Cloudinary |
| Credenciales PostgreSQL | Según configuración de Render |

> **Correo:** No uses SMTP en Render (puerto 587 suele bloquearse). El envío usa la API HTTP de Resend (`usuarios/email_service.py`). Para que **cualquier usuario** reciba el correo, verifica un dominio propio en Resend. Guía: [docs/EMAIL_RESEND.md](docs/EMAIL_RESEND.md).

### Checklist

- [x] `DEBUG=False`, `SECRET_KEY` y DB por entorno
- [x] `CORS_ALLOWED_ORIGINS` con URL de Vercel
- [x] Cloudinary configurado
- [x] Correo vía API Resend (sin SMTP)
- [ ] Dominio verificado en Resend + `RESEND_FROM_EMAIL` (envío a correos públicos)
- [ ] Redis (opcional) si hay varios workers y se requiere throttling consistente entre procesos

---

## Control de versiones (GitFlow)

- `main` — estable
- `develop` — integración
- `feature/<nombre>` — desarrollo

Cambios vía Pull Request; no push directo a `main` ni `develop`.

---

## Datos iniciales

**Municipios (15):** Riohacha, Albania, Barrancas, Dibulla, Distracción, El Molino, Fonseca, Hatonuevo, La Jagua del Pilar, Maicao, Manaure, San Juan del Cesar, Uribia, Urumita, Villanueva.

**Categorías (8):** Frutas, Verduras y hortalizas, Tubérculos y raíces, Granos y cereales, Lácteos, Carnes y aves, Hierbas y condimentos, Otros.

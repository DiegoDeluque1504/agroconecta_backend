# AgroConecta — Backend

API REST para la plataforma de comercialización agrícola directa para pequeños productores del departamento de La Guajira, Colombia.

---

## Descripción general

AgroConecta conecta productores agrícolas con compradores eliminando intermediarios. Los productores publican sus productos, los compradores los encuentran a través del catálogo y negocian directamente a través de un canal de chat asíncrono.

---

## Integrantes

| Nombre | Rol |
|---|---|
| Diego De Luque |
| Carlos Basilio | 
| David Royero | 
| Daniel Royero | 

**Institución:** Universidad de La Guajira  
**Programa:** Ingeniería de Sistemas  
**Asignatura:** Ingeniería de software II

---

## Stack tecnológico

| Tecnología | Uso |
|---|---|
| Python 3.10+ | Lenguaje de programación |
| Django 4.x | Framework web |
| Django REST Framework | API REST |
| PostgreSQL 15 | Base de datos |
| Docker | Contenedor de base de datos |
| WSL 2 (Ubuntu) | Entorno de desarrollo |
| JWT (SimpleJWT) | Autenticación |
| Cloudinary | Almacenamiento de imágenes y audios |
| Railway | Despliegue en producción (futuro) |

---

## Arquitectura del proyecto

```
agroconectabackend/
├── config/                  # Configuración central de Django
│   ├── settings.py          # Configuración general
│   ├── urls.py              # URLs principales
│   └── wsgi.py
├── usuarios/                # Autenticación y perfiles
│   ├── models.py            # Usuario, Municipio, TokenVerificacion
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── fixtures/
│       └── municipios.json  # 15 municipios de La Guajira
├── productos/               # Catálogo de productos
│   ├── models.py            # Producto, CategoriaProducto, FotoProducto
│   ├── serializers.py
│   ├── views.py
│   ├── permissions.py
│   ├── urls.py
│   └── fixtures/
│       └── categorias.json  # 8 categorías agrícolas
├── negociacion/             # Chat entre comprador y productor
│   ├── models.py            # Negociacion, Mensaje
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── pedidos/                 # Gestión de pedidos y calificaciones
│   ├── models.py            # Pedido, HistorialEstadoPedido, Calificacion
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── notificaciones/          # Notificaciones persistentes
│   ├── models.py            # Notificacion
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── utils.py             # Función crear_notificacion()
├── manage.py
└── requirements.txt
```

---

## Modelos de base de datos

### Municipio
Tabla de referencia precargada con los 15 municipios oficiales de La Guajira según el DANE.

### Usuario
Extiende `AbstractUser` de Django. Un usuario puede tener rol de productor, comprador o ambos simultáneamente.

| Campo | Tipo | Descripción |
|---|---|---|
| email | EmailField | Identificador principal (único) |
| es_productor | Boolean | Puede publicar productos |
| es_comprador | Boolean | Puede iniciar negociaciones |
| email_verificado | Boolean | Cuenta activa tras verificación |
| telefono | CharField | Contacto |
| latitud / longitud | Decimal | Geolocalización del productor |
| calificacion_promedio | Decimal | Promedio calculado automáticamente |
| municipio | FK → Municipio | Municipio de residencia |

### Producto

| Campo | Tipo | Descripción |
|---|---|---|
| nombre | CharField | Nombre del producto |
| descripcion | TextField | Descripción detallada |
| precio | Decimal | Precio en pesos colombianos |
| cantidad_disponible | Decimal | Stock disponible |
| unidad_medida | TextChoices | kg, lb, und, bulto, lt, arroba |
| estado | TextChoices | activo, agotado, inactivo |
| usuario | FK → Usuario | Productor dueño |
| categoria | FK → CategoriaProducto | Categoría fija |
| municipio | FK → Municipio | Municipio de disponibilidad |

### Negociacion
Hilo de chat entre comprador y productor sobre un producto específico.

| Estado | Descripción |
|---|---|
| abierta | En curso, acepta mensajes |
| cerrada | Se generó un pedido |
| cancelada | Cancelada por cualquiera de las partes |

### Mensaje

| Campo | Tipo | Descripción |
|---|---|---|
| tipo | TextChoices | texto, audio |
| contenido | TextField | Texto del mensaje |
| url_audio | URLField | URL del audio en Cloudinary |
| leido | Boolean | Estado de lectura |

### Pedido
Registro formal del acuerdo. Nace cuando el productor formaliza una negociación.

| Estado | Descripción |
|---|---|
| confirmado | Pedido creado |
| en_preparacion | Productor preparando |
| en_camino | En camino al comprador |
| entregado | Entrega completada |
| cancelado | Cancelado por cualquiera |

### Calificacion
Calificación mutua entre comprador y productor. Solo disponible después de entrega. Una calificación por usuario por pedido.

---

## Instalación y configuración local

### Requisitos previos
- Windows con WSL 2 (Ubuntu)
- Docker instalado dentro de WSL
- Python 3.10 o superior
- Git

### Paso 1 — Levantar PostgreSQL en Docker

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

### Paso 2 — Clonar el repositorio

```bash
git clone https://github.com/DiegoDeluque1504/agroconecta_backend.git
cd agroconecta_backend
```

### Paso 3 — Crear entorno virtual e instalar dependencias

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Paso 4 — Crear el archivo .env

Crea el archivo `.env` en la raíz del proyecto con este contenido:

```
SECRET_KEY=django-insecure-clave-temporal-cambiar-en-produccion
DEBUG=True
DB_NAME=agroconecta_db
DB_USER=agroconecta_user
DB_PASSWORD=agroconecta2026
DB_HOST=localhost
DB_PORT=5432
CLOUDINARY_CLOUD_NAME=tu_cloud_name
CLOUDINARY_API_KEY=tu_api_key
CLOUDINARY_API_SECRET=tu_api_secret
```

> ⚠️ El archivo `.env` nunca debe subirse a GitHub. Ya está incluido en `.gitignore`.

### Paso 5 — Correr migraciones y cargar datos iniciales

```bash
python manage.py migrate
python manage.py loaddata usuarios/fixtures/municipios.json
python manage.py loaddata productos/fixtures/categorias.json
```

### Paso 6 — Arrancar el servidor

```bash
python manage.py runserver
```

El servidor queda disponible en `http://127.0.0.1:8000/`

### Comandos del día a día

```bash
sudo service docker start
docker start agroconecta_db
cd ~/agroconecta_backend
source venv/bin/activate
python manage.py runserver
```

---

## Endpoints de la API

Base URL: `http://127.0.0.1:8000/api/v1/`

### Usuarios

| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| POST | `usuarios/registro/` | Registrar nuevo usuario | No |
| POST | `usuarios/verificar-email/` | Verificar correo con token | No |
| POST | `usuarios/login/` | Iniciar sesión | No |
| POST | `usuarios/token/refresh/` | Renovar token JWT | No |
| GET/PUT | `usuarios/perfil/` | Ver y editar perfil | Sí |
| GET | `usuarios/municipios/` | Listar municipios de La Guajira | No |

### Productos

| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| GET | `productos/categorias/` | Listar categorías | No |
| GET | `productos/catalogo/` | Catálogo con filtros | No |
| GET | `productos/<id>/` | Detalle de producto | No |
| POST | `productos/crear/` | Publicar producto | Productor |
| PUT | `productos/<id>/gestionar/` | Editar producto | Productor dueño |
| DELETE | `productos/<id>/gestionar/` | Eliminar producto | Productor dueño |
| POST | `productos/<id>/fotos/agregar/` | Agregar foto | Productor dueño |
| DELETE | `productos/fotos/<id>/eliminar/` | Eliminar foto | Productor dueño |
| GET | `productos/mis-productos/` | Productos del productor | Productor |

#### Filtros del catálogo

```
GET /api/v1/productos/catalogo/?categoria=1
GET /api/v1/productos/catalogo/?municipio=7
GET /api/v1/productos/catalogo/?precio_min=1000&precio_max=5000
GET /api/v1/productos/catalogo/?busqueda=mango
GET /api/v1/productos/catalogo/?categoria=1&municipio=7&precio_max=5000
```

### Negociaciones

| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| POST | `negociaciones/iniciar/<producto_id>/` | Iniciar negociación | Sí |
| GET | `negociaciones/mis-negociaciones/` | Listar negociaciones | Sí |
| GET | `negociaciones/<id>/` | Detalle con mensajes | Sí |
| POST | `negociaciones/<id>/mensajes/` | Enviar mensaje | Sí |
| POST | `negociaciones/<id>/estado/` | Cambiar estado | Sí |

### Pedidos

| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| POST | `pedidos/crear/<negociacion_id>/` | Crear pedido | Productor |
| GET | `pedidos/mis-pedidos/` | Listar pedidos | Sí |
| GET | `pedidos/<id>/` | Detalle de pedido | Sí |
| POST | `pedidos/<id>/estado/` | Actualizar estado | Sí |
| POST | `pedidos/<id>/calificar/` | Calificar tras entrega | Sí |

### Notificaciones

| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| GET | `notificaciones/` | Listar notificaciones | Sí |
| GET | `notificaciones/no-leidas/` | Conteo de no leídas | Sí |
| POST | `notificaciones/<id>/leer/` | Marcar como leída | Sí |
| POST | `notificaciones/leer-todas/` | Marcar todas como leídas | Sí |

---

## Flujos principales

### Flujo de registro y autenticación

```
1. POST /usuarios/registro/        → Cuenta creada inactiva
2. Token enviado a consola (dev)   → Token de verificación
3. POST /usuarios/verificar-email/ → Cuenta activada + tokens JWT
4. POST /usuarios/login/           → Tokens JWT
5. GET  /usuarios/perfil/          → Con header Authorization: Bearer <token>
```

### Flujo de compra completo

```
1. GET  /productos/catalogo/              → Comprador encuentra producto
2. POST /negociaciones/iniciar/<id>/      → Comprador inicia negociación
3. POST /negociaciones/<id>/mensajes/     → Intercambio de mensajes
4. POST /pedidos/crear/<negociacion_id>/  → Productor formaliza el pedido
5. POST /pedidos/<id>/estado/             → Productor actualiza estados
6. POST /pedidos/<id>/calificar/          → Ambos se califican mutuamente
```

### Flujo de notificaciones

Las notificaciones se generan automáticamente en estos eventos:

- Mensaje nuevo en una negociación
- Pedido confirmado
- Cambio de estado del pedido
- Calificación recibida

---

## Autenticación

La API usa JWT (JSON Web Tokens). Incluir en cada petición protegida:

```
Authorization: Bearer <access_token>
```

El token de acceso expira en **1 hora**. Para renovarlo sin hacer login:

```
POST /api/v1/usuarios/token/refresh/
Body: { "refresh": "<refresh_token>" }
```

El token de refresco expira en **7 días**.

---

## Control de versiones

El proyecto usa GitFlow:

- `main` — código estable y probado
- `develop` — integración de funcionalidades
- `feature/<nombre>` — ramas de desarrollo individual

**Reglas:**
- Nunca hacer push directo a `main` ni `develop`
- Todo cambio va por Pull Request
- Al menos un integrante debe revisar antes de hacer merge

---

## Datos iniciales precargados

### Municipios de La Guajira
Riohacha, Albania, Barrancas, Dibulla, Distracción, El Molino, Fonseca, Hatonuevo, La Jagua del Pilar, Maicao, Manaure, San Juan del Cesar, Uribia, Urumita, Villanueva.

### Categorías de productos
Frutas, Verduras y hortalizas, Tubérculos y raíces, Granos y cereales, Lácteos, Carnes y aves, Hierbas y condimentos, Otros.

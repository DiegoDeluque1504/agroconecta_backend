# Correo con Resend — enviar a cualquier usuario

## Por qué no basta con `onboarding@resend.dev`

Esa dirección es **solo de prueba** de Resend. Con ella solo puedes enviar a **tu propio correo** (el de la cuenta de Resend), no a productores o compradores reales.

Para que **cualquier persona** con un correo válido reciba el mensaje de verificación, Resend exige que verifiques **un dominio que controles** (ej. `agroconecta.com` o un subdominio).

No es una limitación de AgroConecta: todos los proveedores serios (Resend, SendGrid, Amazon SES) funcionan igual.

---

## Pasos (una sola vez)

### 1. Tener un dominio

Opciones habituales para un proyecto académico:

- Comprar un dominio barato (`.com`, `.co`, etc.) en Namecheap, Google Domains, Hostinger, etc.
- Usar un dominio que ya tenga el equipo o la universidad (con permiso para añadir registros DNS).

### 2. Verificar el dominio en Resend

1. Entra en [resend.com/domains](https://resend.com/domains).
2. **Add Domain** → escribe tu dominio (ej. `agroconecta.com`).
3. Resend te muestra registros DNS (SPF, DKIM, etc.).
4. En el panel de tu registrador de dominio, crea esos registros TXT/CNAME.
5. Espera a que Resend marque el dominio como **Verified** (puede tardar minutos u horas).

### 3. Configurar Render

En el servicio del backend → **Environment**, añade o actualiza:

| Variable | Ejemplo |
|----------|---------|
| `RESEND_API_KEY` | `re_xxxxxxxx` |
| `RESEND_FROM_EMAIL` | `AgroConecta <noreply@agroconecta.com>` |
| `FRONTEND_URL` | `https://agroconecta-frontend-sigma.vercel.app` |

La parte antes de `@` puede ser cualquier nombre (`noreply`, `hola`, `verificacion`); **no hace falta** crear esa bandeja en un servidor de correo.

**No uses** `onboarding@resend.dev` en producción.

### 4. Redeploy

Guarda las variables y deja que Render redespliegue el backend.

### 5. Probar

Registra un usuario con un Gmail, Outlook, etc. distinto al de tu cuenta Resend. Debe llegar el correo (revisa spam la primera vez).

---

## Desarrollo local

Con `DEBUG=True` puedes dejar `onboarding@resend.dev` o no definir `RESEND_FROM_EMAIL`; sin API key el enlace se imprime en consola.

---

## Límites del plan gratuito de Resend

Suele permitir unos **100 correos/día** en plan free, suficiente para un proyecto académico. Consulta [resend.com/pricing](https://resend.com/pricing).

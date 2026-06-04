# Recordatorios sin pagar Render Cron

## Lo que ya funciona gratis (sin cron)

Con el backend desplegado en Render **gratis**:

| Evento | Correo automático |
|--------|-------------------|
| Mensaje nuevo, pedido, calificación | Sí, al instante |
| Login desde dispositivo nuevo | Sí |

No necesitas cron para eso.

## Lo que sí usa el “cron” (opcional)

Solo el **recordatorio** si un mensaje sigue **sin leer más de 10 minutos** (correo consolidado extra).

Si no configuras cron externo, igual recibes el correo **inmediato** al llegar el mensaje.

---

## Opción recomendada: cron-job.org (gratis)

1. Crea cuenta en [cron-job.org](https://cron-job.org).
2. **Create cronjob**:
   - **URL:**  
     `https://TU-BACKEND.onrender.com/api/v1/negociaciones/cron/recordatorios/?secret=TU_CRON_SECRET`
   - **Schedule:** cada 10 minutos → `*/10 * * * *`
   - **Request method:** GET (o POST)
3. En Render (servicio **web** del backend), añade variable de entorno:
   - `CRON_SECRET` = una contraseña larga aleatoria (ej. generada con un gestor de contraseñas)
4. Redeploy del backend.
5. En cron-job.org, prueba **Run now** → debe responder JSON como:
   ```json
   {"enviados": 0, "fallidos": 0, "mensaje": "No hay mensajes pendientes por notificar."}
   ```

Sustituye `TU-BACKEND` por tu host real (ej. `agroconecta-backend-sjmy.onrender.com`).

---

## Opción 2: GitHub Actions (gratis)

En el repo, crea `.github/workflows/recordatorios.yml`:

```yaml
name: Recordatorios AgroConecta
on:
  schedule:
    - cron: '*/10 * * * *'
  workflow_dispatch:

jobs:
  recordatorios:
    runs-on: ubuntu-latest
    steps:
      - name: Ejecutar recordatorios
        run: |
          curl -fsS "https://TU-BACKEND.onrender.com/api/v1/negociaciones/cron/recordatorios/?secret=${{ secrets.CRON_SECRET }}"
```

En GitHub → **Settings → Secrets → Actions** → `CRON_SECRET` (mismo valor que en Render).

---

## Seguridad

- No compartas la URL con el `secret` en público.
- Usa un `CRON_SECRET` largo y distinto de `SECRET_KEY`.

---

## Comando manual (desarrollo)

```bash
python manage.py enviar_recordatorios
```

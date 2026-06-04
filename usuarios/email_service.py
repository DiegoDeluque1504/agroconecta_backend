import logging
import threading

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class EmailSendError(Exception):
    """Error al enviar correo (Resend API o configuración)."""

    def __init__(self, message, status_code=None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _validar_configuracion_correo():
    """En producción exige remitente de un dominio verificado en Resend."""
    remitente = (settings.DEFAULT_FROM_EMAIL or '').lower()
    if settings.DEBUG:
        return
    if not remitente or 'resend.dev' in remitente:
        raise EmailSendError(
            'Correo no configurado para producción. Define RESEND_FROM_EMAIL en Render '
            'con una dirección de un dominio verificado en Resend '
            '(por ejemplo: AgroConecta <noreply@tudominio.com>). '
            'Ver docs/EMAIL_RESEND.md.'
        )


def _mensaje_error_resend(status_code, response_text):
    texto = (response_text or '').lower()
    if status_code == 403 or 'verify a domain' in texto or 'only send' in texto:
        return (
            'El servicio de correo no puede enviar a este destinatario. '
            'El administrador debe verificar un dominio propio en Resend.'
        )
    return 'No se pudo enviar el correo. Intenta más tarde.'


def _enviar_correo_resend(destinatario, subject, html, *, raise_on_error=False):
    """
    Envía un correo vía API HTTP de Resend.
    Si raise_on_error=False, registra el error y no lanza excepción (notificaciones/alertas).
    """
    _validar_configuracion_correo()

    api_key = settings.RESEND_API_KEY
    if not api_key:
        if settings.DEBUG:
            logger.warning(
                '[DEV] RESEND_API_KEY no configurada. Correo no enviado a %s — asunto: %s',
                destinatario,
                subject,
            )
            return {'id': 'dev-console'}
        if raise_on_error:
            raise EmailSendError(
                'El servicio de correo no está configurado. Contacta al administrador.'
            )
        logger.error('RESEND_API_KEY no configurada; correo no enviado a %s', destinatario)
        return None

    payload = {
        'from': settings.DEFAULT_FROM_EMAIL,
        'to': [destinatario],
        'subject': subject,
        'html': html,
    }

    try:
        response = requests.post(
            'https://api.resend.com/emails',
            json=payload,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            timeout=15,
        )
    except requests.RequestException as exc:
        logger.exception('Error de red al enviar correo con Resend a %s', destinatario)
        if raise_on_error:
            raise EmailSendError(
                'No se pudo conectar con el servicio de correo. Intenta más tarde.'
            ) from exc
        return None

    if response.status_code >= 400:
        logger.error(
            'Resend API respondió %s para %s: %s',
            response.status_code,
            destinatario,
            response.text,
        )
        if raise_on_error:
            raise EmailSendError(
                _mensaje_error_resend(response.status_code, response.text),
                status_code=response.status_code,
            )
        return None

    return response.json()


def enviar_correo_verificacion(destinatario, nombre, enlace_verificacion):
    """Correo de verificación de cuenta (falla en registro si no se puede enviar)."""
    html = f'''
        <h2>Hola {nombre},</h2>
        <p>Gracias por registrarte en <strong>AgroConecta</strong>.</p>
        <p>Para activar tu cuenta, haz clic en el siguiente enlace:</p>
        <p><a href="{enlace_verificacion}">Verificar mi cuenta</a></p>
        <p>Este enlace expira en 24 horas.</p>
        <p>Si no creaste esta cuenta, ignora este mensaje.</p>
    '''
    return _enviar_correo_resend(
        destinatario,
        'Verifica tu correo en AgroConecta',
        html,
        raise_on_error=True,
    )


def enviar_alerta_nuevo_dispositivo(destinatario, nombre, ip, navegador, sistema_operativo, fecha_hora):
    """Alerta automática al iniciar sesión desde un dispositivo nuevo."""
    html = f'''
        <h2>Hola {nombre},</h2>
        <p>Se detectó un inicio de sesión desde un nuevo dispositivo en tu cuenta de <strong>AgroConecta</strong>.</p>
        <p><strong>Detalles del inicio de sesión:</strong></p>
        <ul>
            <li><strong>Sistema Operativo:</strong> {sistema_operativo}</li>
            <li><strong>Navegador:</strong> {navegador}</li>
            <li><strong>Dirección IP:</strong> {ip}</li>
            <li><strong>Fecha y Hora:</strong> {fecha_hora.strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
        </ul>
        <p>Si fuiste tú, no es necesario realizar ninguna acción.</p>
        <p>Si no reconoces este inicio de sesión, cambia tu contraseña desde tu perfil.</p>
        <br>
        <p>El equipo de AgroConecta</p>
    '''
    _enviar_correo_resend(
        destinatario,
        'Inicio de sesión desde un nuevo dispositivo - AgroConecta',
        html,
        raise_on_error=False,
    )


def enviar_correo_notificacion(destinatario, nombre, titulo, mensaje, url_destino=None):
    """Correo automático al crear una notificación in-app."""
    enlace = ''
    if url_destino:
        ruta = url_destino if url_destino.startswith('/') else f'/{url_destino}'
        enlace = f'<p><a href="{settings.FRONTEND_URL}{ruta}">Ver en AgroConecta</a></p>'

    html = f'''
        <h2>Hola {nombre},</h2>
        <p><strong>{titulo}</strong></p>
        <p>{mensaje}</p>
        {enlace}
        <br>
        <p>El equipo de AgroConecta</p>
    '''
    _enviar_correo_resend(
        destinatario,
        f'{titulo} - AgroConecta',
        html,
        raise_on_error=False,
    )


def enviar_correo_recordatorio(destinatario, nombre, detalles_html):
    """Correo consolidado de mensajes no leídos (comando programado)."""
    html = f'''
        <h2>Hola {nombre},</h2>
        <p>Tienes mensajes sin leer en <strong>AgroConecta</strong> recibidos hace más de 10 minutos:</p>
        {detalles_html}
        <p><a href="{settings.FRONTEND_URL}/negociaciones">Ir a mis negociaciones</a></p>
        <br>
        <p>El equipo de AgroConecta</p>
    '''
    return _enviar_correo_resend(
        destinatario,
        'Tienes nuevos mensajes pendientes en AgroConecta',
        html,
        raise_on_error=False,
    )


def enviar_correo_en_segundo_plano(func, *args, **kwargs):
    """Ejecuta un envío de correo sin bloquear la petición HTTP."""
    threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()

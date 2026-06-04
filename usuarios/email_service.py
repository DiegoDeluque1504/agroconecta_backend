import logging

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
    return 'No se pudo enviar el correo de verificación. Intenta más tarde.'


def enviar_correo_verificacion(destinatario, nombre, enlace_verificacion):
    """
    Envía el correo de verificación vía API HTTP de Resend.
    Render y otros PaaS suelen bloquear SMTP (puerto 587); la API evita timeouts.
    """
    _validar_configuracion_correo()

    api_key = settings.RESEND_API_KEY
    if not api_key:
        if settings.DEBUG:
            logger.warning(
                '[DEV] RESEND_API_KEY no configurada. Enlace de verificación: %s',
                enlace_verificacion,
            )
            print(f'[DEV] Enlace de verificación: {enlace_verificacion}')
            return {'id': 'dev-console'}
        raise EmailSendError(
            'El servicio de correo no está configurado. Contacta al administrador.'
        )

    payload = {
        'from': settings.DEFAULT_FROM_EMAIL,
        'to': [destinatario],
        'subject': 'Verifica tu correo en AgroConecta',
        'html': f'''
        <h2>Hola {nombre},</h2>
        <p>Gracias por registrarte en <strong>AgroConecta</strong>.</p>
        <p>Para activar tu cuenta, haz clic en el siguiente enlace:</p>
        <p><a href="{enlace_verificacion}">Verificar mi cuenta</a></p>
        <p>Este enlace expira en 24 horas.</p>
        <p>Si no creaste esta cuenta, ignora este mensaje.</p>
        ''',
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
        logger.exception('Error de red al enviar correo con Resend')
        raise EmailSendError(
            'No se pudo conectar con el servicio de correo. Intenta más tarde.'
        ) from exc

    if response.status_code >= 400:
        logger.error(
            'Resend API respondió %s: %s',
            response.status_code,
            response.text,
        )
        raise EmailSendError(
            _mensaje_error_resend(response.status_code, response.text),
            status_code=response.status_code,
        )

    return response.json()


def enviar_alerta_nuevo_dispositivo(destinatario, nombre, ip, navegador, sistema_operativo, fecha_hora):
    """
    Envía una alerta de inicio de sesión desde un nuevo dispositivo vía API de Resend.
    """
    _validar_configuracion_correo()

    api_key = settings.RESEND_API_KEY
    if not api_key:
        if settings.DEBUG:
            logger.warning(
                '[DEV] RESEND_API_KEY no configurada. Alerta de nuevo dispositivo para %s: IP=%s, Nav=%s, OS=%s',
                destinatario, ip, navegador, sistema_operativo
            )
            return {'id': 'dev-console'}
        return

    payload = {
        'from': settings.DEFAULT_FROM_EMAIL,
        'to': [destinatario],
        'subject': 'Inicio de sesión desde un nuevo dispositivo - AgroConecta',
        'html': f'''
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
        <p>Si no reconoces este inicio de sesión, te recomendamos cambiar tu contraseña inmediatamente desde tu perfil para asegurar tu cuenta.</p>
        <br>
        <p>El equipo de AgroConecta</p>
        ''',
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
        if response.status_code >= 400:
            logger.error(
                'Resend API de Alerta respondió %s: %s',
                response.status_code,
                response.text,
            )
    except requests.RequestException:
        logger.exception('Error de red al enviar correo de alerta de nuevo dispositivo con Resend')


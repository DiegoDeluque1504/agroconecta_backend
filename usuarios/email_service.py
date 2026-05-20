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


def enviar_correo_verificacion(destinatario, nombre, enlace_verificacion):
    """
    Envía el correo de verificación vía API HTTP de Resend.
    Render y otros PaaS suelen bloquear SMTP (puerto 587); la API evita timeouts.
    """
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
            'No se pudo enviar el correo de verificación. Intenta más tarde.',
            status_code=response.status_code,
        )

    return response.json()

import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def validar_captcha(token, ip=None):
    """
    Valida un token de Cloudflare Turnstile contra la API de Cloudflare.
    Si TURNSTILE_SECRET_KEY no está configurada, en modo DEBUG/desarrollo permite pasar.
    """
    secret_key = settings.TURNSTILE_SECRET_KEY
    if not secret_key:
        if settings.DEBUG:
            logger.warning("TURNSTILE_SECRET_KEY no configurada. Omitiendo validación de CAPTCHA en desarrollo/local.")
            return True
        logger.error("TURNSTILE_SECRET_KEY no configurada en producción. Rechazando validación.")
        return False
        
    if not token:
        logger.warning("Intento de validación de CAPTCHA sin proveer un token.")
        return False
        
    payload = {
        'secret': secret_key,
        'response': token,
    }
    if ip:
        payload['remoteip'] = ip
        
    try:
        response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data=payload,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            success = result.get('success', False)
            if not success:
                logger.warning(f"Validación de CAPTCHA fallida: {result.get('error-codes', 'Sin códigos de error')}")
            return success
        logger.error(f"La API de Turnstile retornó código {response.status_code}: {response.text}")
        return False
    except requests.RequestException:
        logger.exception("Error al conectar con la API de Cloudflare Turnstile")
        return False

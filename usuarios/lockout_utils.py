"""
Utilidades para respuestas de bloqueo de django-axes en formato JSON
consumible por el frontend Angular.
"""
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from axes.handlers.proxy import AxesProxyHandler
from axes.helpers import get_client_ip_address, get_client_username, get_cool_off, get_credentials
from axes.models import AccessAttempt


def format_wait_time(seconds: int) -> str:
    """Convierte segundos a texto legible en español."""
    if seconds >= 3600:
        hours = seconds // 3600
        remainder = seconds % 3600
        if remainder >= 60:
            minutes = remainder // 60
            hora_txt = 'hora' if hours == 1 else 'horas'
            min_txt = 'minuto' if minutes == 1 else 'minutos'
            return f'{hours} {hora_txt} y {minutes} {min_txt}'
        hora_txt = 'hora' if hours == 1 else 'horas'
        return f'{hours} {hora_txt}'
    if seconds >= 60:
        minutes = max(1, seconds // 60)
        min_txt = 'minuto' if minutes == 1 else 'minutos'
        return f'{minutes} {min_txt}'
    seg_txt = 'segundo' if seconds == 1 else 'segundos'
    return f'{seconds} {seg_txt}'


def get_remaining_lockout_seconds(request, credentials=None) -> int:
    """Calcula los segundos restantes del bloqueo para la IP/usuario actual."""
    AxesProxyHandler.update_request(request)
    cool_off = get_cool_off(request)
    if not cool_off:
        return 3600

    ip = get_client_ip_address(request)
    username = get_client_username(request, credentials)

    attempts = AccessAttempt.objects.filter(ip_address=ip)
    if username:
        attempts = attempts.filter(username=username)

    attempt = attempts.select_related('expiration').order_by('-attempt_time').first()
    if not attempt:
        return int(cool_off.total_seconds())

    if hasattr(attempt, 'expiration') and attempt.expiration_id:
        remaining = (attempt.expiration.expires_at - timezone.now()).total_seconds()
        return max(0, int(remaining))

    elapsed = (timezone.now() - attempt.attempt_time).total_seconds()
    return max(0, int(cool_off.total_seconds() - elapsed))


def build_lockout_message(remaining_seconds: int) -> str:
    wait = format_wait_time(remaining_seconds)
    return (
        'Demasiados intentos fallidos. Tu acceso ha sido bloqueado temporalmente. '
        f'Intenta nuevamente dentro de {wait}.'
    )


def lockout_payload(request, credentials=None) -> dict:
    remaining = get_remaining_lockout_seconds(request, credentials)
    detail = build_lockout_message(remaining)
    return {
        'code': 'axes_lockout',
        'error': detail,
        'detail': detail,
        'cooloff_seconds': remaining,
    }


def lockout_api_response(request, credentials=None) -> Response:
    """Respuesta DRF para el endpoint de login cuando la IP está bloqueada."""
    return Response(
        lockout_payload(request, credentials),
        status=status.HTTP_429_TOO_MANY_REQUESTS,
    )


def axes_lockout_callable(request, response=None, credentials=None):
    """
    Callable para AXES_LOCKOUT_CALLABLE.
    El middleware de axes usa esto cuando reemplaza la respuesta tras un bloqueo.
    """
    return JsonResponse(
        lockout_payload(request, credentials),
        status=status.HTTP_429_TOO_MANY_REQUESTS,
    )

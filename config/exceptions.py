"""
Manejador central de excepciones de la API.

Diferencia:
- guest_exploration_limit → visitante anónimo en modo restringido (conversión)
- api_rate_limit          → usuario autenticado superó su cuota diaria
- axes_lockout            → bloqueo de seguridad por intentos de login (vista login)
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from rest_framework import status
from rest_framework.response import Response


GUEST_EXPLORATION_MESSAGE = (
    'Has alcanzado el límite de exploración para usuarios invitados. '
    'Para continuar usando la plataforma, inicia sesión o crea una cuenta.'
)

API_RATE_LIMIT_MESSAGE = (
    'Has superado el límite de peticiones diarias de tu cuenta. '
    'Intenta nuevamente más tarde.'
)


class GuestExplorationLimitExceeded(Exception):
    """Visitante anónimo que agotó su cuota de exploración (no es un bloqueo de IP)."""
    pass


def custom_exception_handler(exc, context):
    if isinstance(exc, GuestExplorationLimitExceeded):
        return Response(
            {
                'code': 'guest_exploration_limit',
                'detail': GUEST_EXPLORATION_MESSAGE,
                'error': GUEST_EXPLORATION_MESSAGE,
            },
            status=status.HTTP_403_FORBIDDEN,
            headers={'X-Guest-Restricted': 'true'},
        )

    response = exception_handler(exc, context)

    if isinstance(exc, Throttled) and response is not None:
        request = context.get('request')
        if request and request.user and request.user.is_authenticated:
            response.data = {
                'code': 'api_rate_limit',
                'detail': API_RATE_LIMIT_MESSAGE,
                'error': API_RATE_LIMIT_MESSAGE,
            }
            response.status_code = status.HTTP_429_TOO_MANY_REQUESTS

    return response

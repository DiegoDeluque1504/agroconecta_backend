"""
Throttling de la API AgroConecta.

- GuestExplorationThrottle: visitantes anónimos (100/día → modo restringido)
- UserRateThrottle: usuarios autenticados (1000/día → 429 tradicional)

Rutas exentas (siempre accesibles sin contar cuota de exploración):
login, registro, verificación de email, refresh JWT, municipios.
"""
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from config.exceptions import GuestExplorationLimitExceeded


# Rutas que no consumen cuota de exploración ni se bloquean en modo restringido
GUEST_EXPLORATION_EXEMPT_PREFIXES = (
    '/api/v1/usuarios/login/',
    '/api/v1/usuarios/registro/',
    '/api/v1/usuarios/verificar-email/',
    '/api/v1/usuarios/token/refresh/',
    '/api/v1/usuarios/municipios/',
)


def is_guest_exploration_exempt(request) -> bool:
    return request.path.startswith(GUEST_EXPLORATION_EXEMPT_PREFIXES)


class GuestExplorationThrottle(AnonRateThrottle):
    """
    Cuota diaria para visitantes no autenticados.
    Al superar el límite lanza GuestExplorationLimitExceeded (403 + código propio),
    no un bloqueo agresivo de IP.
    """
    scope = 'guest_exploration'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return None
        if is_guest_exploration_exempt(request):
            return None
        return super().get_cache_key(request, view)

    def throttle_failure(self):
        raise GuestExplorationLimitExceeded()


class AuthenticatedUserRateThrottle(UserRateThrottle):
    """Rate limit tradicional para usuarios autenticados (1000/día)."""
    scope = 'user'

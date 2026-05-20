from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from axes.handlers.proxy import AxesProxyHandler
from axes.helpers import get_credentials
from .lockout_utils import lockout_api_response
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import uuid
import secrets
from datetime import timedelta

from .models import Usuario, Municipio, TokenVerificacion
from .serializers import (
    RegistroSerializer,
    UsuarioPerfilSerializer,
    MunicipioSerializer,
    VerificacionEmailSerializer,
    LoginSerializer,
    CambiarPasswordSerializer,
)


def _tiene_token_verificacion_activo(email: str) -> bool:
    """
    True si el correo pertenece a una cuenta sin verificar con un token
    de verificación vigente (no usado y sin expirar).
    """
    try:
        usuario = Usuario.objects.select_related('token_verificacion').get(email=email)
    except Usuario.DoesNotExist:
        return False

    if usuario.email_verificado or usuario.is_active:
        return False

    token = getattr(usuario, 'token_verificacion', None)
    if not token or token.usado:
        return False

    return timezone.now() <= token.expira_en


@api_view(['POST'])
@permission_classes([AllowAny])
def registro(request):
    """
    Endpoint para registrar un nuevo usuario.
    Crea la cuenta inactiva y genera un token de verificación
    que se imprime en la consola durante desarrollo.
    """
    email = (request.data.get('email') or '').strip().lower()

    if email and _tiene_token_verificacion_activo(email):
        return Response(
            {
                'code': 'token_activo',
                'error': (
                    'Ya existe una solicitud de registro pendiente para este correo. '
                    'Revisa tu bandeja de entrada o espera 24 horas antes de volver a intentarlo.'
                ),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = RegistroSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    usuario = serializer.save()

    # Genera un token de verificación seguro
    token_str = secrets.token_urlsafe(32)
    expiracion = timezone.now() + timedelta(hours=24)

    TokenVerificacion.objects.create(
        usuario=usuario,
        token=token_str,
        expira_en=expiracion
    )

    # Durante desarrollo, el correo se imprime en la consola de Django
    # En producción esto enviará un correo real
    send_mail(
        subject='Verifica tu correo en AgroConecta',
        message=f'''
Hola {usuario.first_name},

Gracias por registrarte en AgroConecta.

Tu token de verificación es: {token_str}

Este token expira en 24 horas.

Si no creaste esta cuenta, ignora este mensaje.
        ''',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[usuario.email],
        fail_silently=False,
    )

    return Response(
        {
            'mensaje': 'Cuenta creada exitosamente. Revisa tu correo para verificar tu cuenta.',
            'email': usuario.email,
        },
        status=status.HTTP_201_CREATED
    )


def generar_tokens_jwt(usuario):
    """
    Genera los tokens JWT de acceso y refresco para un usuario.
    Se reutiliza en el login y después de verificar el correo.
    """
    refresh = RefreshToken.for_user(usuario)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def verificar_email(request):
    """
    Endpoint para verificar el correo electrónico con el token recibido.
    Activa la cuenta y devuelve los tokens JWT para que el usuario
    quede autenticado inmediatamente después de verificar.
    """
    serializer = VerificacionEmailSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    token_str = serializer.validated_data['token']

    try:
        token = TokenVerificacion.objects.get(token=token_str)
    except TokenVerificacion.DoesNotExist:
        return Response(
            {'error': 'Token inválido.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validaciones del token
    if token.usado:
        return Response(
            {'error': 'Este token ya fue utilizado.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if timezone.now() > token.expira_en:
        return Response(
            {'error': 'El token ha expirado. Solicita uno nuevo.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Activa la cuenta del usuario
    usuario = token.usuario
    usuario.is_active = True
    usuario.email_verificado = True
    usuario.save()

    # Marca el token como usado
    token.usado = True
    token.save()

    # Devuelve los tokens JWT para autenticar inmediatamente
    tokens = generar_tokens_jwt(usuario)

    return Response(
        {
            'mensaje': 'Correo verificado exitosamente. ¡Bienvenido a AgroConecta!',
            'tokens': tokens,
            'usuario': UsuarioPerfilSerializer(usuario).data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Endpoint de inicio de sesión.
    Recibe email y contraseña, devuelve tokens JWT si las credenciales son válidas.
    """
    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data['email']
    password = serializer.validated_data['password']
    credentials = get_credentials(username=email, password=password)

    # Bloqueo por django-axes (demasiados intentos fallidos)
    if AxesProxyHandler.is_locked(request, credentials):
        return lockout_api_response(request, credentials)

    # Django busca el usuario y verifica la contraseña encriptada
    usuario = authenticate(request, username=email, password=password)

    if usuario is None:
        # Tras un intento fallido, puede activarse el bloqueo en esta misma petición
        if AxesProxyHandler.is_locked(request, credentials):
            return lockout_api_response(request, credentials)
        return Response(
            {
                'code': 'invalid_credentials',
                'error': 'Correo o contraseña incorrectos.',
                'detail': 'Correo o contraseña incorrectos.',
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not usuario.email_verificado:
        return Response(
            {'error': 'Debes verificar tu correo electrónico antes de iniciar sesión.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if not usuario.is_active:
        return Response(
            {'error': 'Tu cuenta está desactivada. Contacta al soporte.'},
            status=status.HTTP_403_FORBIDDEN
        )

    tokens = generar_tokens_jwt(usuario)

    return Response(
        {
            'tokens': tokens,
            'usuario': UsuarioPerfilSerializer(usuario).data,
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def perfil(request):
    """
    Endpoint para ver y editar el perfil del usuario autenticado.
    GET: devuelve los datos del perfil.
    PUT: actualiza los datos del perfil.
    """
    usuario = request.user

    if request.method == 'GET':
        serializer = UsuarioPerfilSerializer(usuario)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = UsuarioPerfilSerializer(
            usuario,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cambiar_password(request):
    """
    Cambia la contraseña del usuario autenticado.
    Requiere la contraseña actual y valida la nueva con las reglas de Django.
    """
    serializer = CambiarPasswordSerializer(
        data=request.data,
        context={'request': request},
    )

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    usuario = request.user
    usuario.set_password(serializer.validated_data['password_nueva'])
    usuario.save()

    return Response(
        {'mensaje': 'Contraseña actualizada correctamente.'},
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_municipios(request):
    """
    Endpoint público para listar todos los municipios de La Guajira.
    Se usa en el formulario de registro para que el usuario elija su municipio.
    """
    municipios = Municipio.objects.all()
    serializer = MunicipioSerializer(municipios, many=True)
    return Response(serializer.data)
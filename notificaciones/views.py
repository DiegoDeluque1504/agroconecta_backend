from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from .models import Notificacion
from .serializers import NotificacionSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_notificaciones(request):
    """
    Lista todas las notificaciones del usuario autenticado.
    Soporta filtro por leídas/no leídas.
    """
    notificaciones = Notificacion.objects.filter(usuario=request.user)

    # Filtro opcional por estado de lectura
    solo_no_leidas = request.query_params.get('no_leidas')
    if solo_no_leidas == 'true':
        notificaciones = notificaciones.filter(leida=False)

    serializer = NotificacionSerializer(notificaciones, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conteo_no_leidas(request):
    """
    Devuelve solo el número de notificaciones no leídas.
    Se usa para mostrar el badge en la interfaz sin cargar todas las notificaciones.
    Optimizado para conexiones lentas: respuesta mínima.
    """
    conteo = Notificacion.objects.filter(
        usuario=request.user,
        leida=False
    ).count()

    return Response({'no_leidas': conteo})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar_leida(request, notificacion_id):
    """
    Marca una notificación específica como leída.
    """
    try:
        notificacion = Notificacion.objects.get(
            id=notificacion_id,
            usuario=request.user
        )
    except Notificacion.DoesNotExist:
        return Response(
            {'error': 'Notificación no encontrada.'},
            status=status.HTTP_404_NOT_FOUND
        )

    notificacion.leida = True
    notificacion.leida_en = timezone.now()
    notificacion.save()

    return Response({'mensaje': 'Notificación marcada como leída.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar_todas_leidas(request):
    """
    Marca todas las notificaciones del usuario como leídas.
    Se usa cuando el usuario abre el panel de notificaciones.
    """
    Notificacion.objects.filter(
        usuario=request.user,
        leida=False
    ).update(leida=True, leida_en=timezone.now())

    return Response({'mensaje': 'Todas las notificaciones marcadas como leídas.'})
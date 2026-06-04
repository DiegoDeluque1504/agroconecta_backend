from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from django.utils import timezone
from notificaciones.utils import crear_notificacion
from file_validators import validar_audio
import cloudinary.uploader

from .models import Negociacion, Mensaje
from .serializers import (
    NegociacionListSerializer,
    NegociacionDetalleSerializer,
    CrearMensajeSerializer,
    MensajeSerializer,
)
from productos.models import Producto


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def iniciar_negociacion(request, producto_id):
    """
    El comprador inicia una negociación sobre un producto.
    No se puede iniciar una negociación sobre un producto propio.
    No se puede tener dos negociaciones abiertas sobre el mismo producto.
    """
    try:
        producto = Producto.objects.get(id=producto_id, estado='activo')
    except Producto.DoesNotExist:
        return Response(
            {'error': 'Producto no encontrado o no está disponible.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Un productor no puede negociar con sus propios productos
    if producto.usuario == request.user:
        return Response(
            {'error': 'No puedes iniciar una negociación sobre tu propio producto.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verifica que no exista una negociación abierta sobre el mismo producto
    negociacion_existente = Negociacion.objects.filter(
        comprador=request.user,
        producto=producto,
        estado='abierta'
    ).first()

    if negociacion_existente:
        return Response(
            {
                'error': 'Ya tienes una negociación abierta sobre este producto.',
                'negociacion_id': negociacion_existente.id,
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    negociacion = Negociacion.objects.create(
        comprador=request.user,
        producto=producto,
        estado='abierta'
    )

    return Response(
        NegociacionDetalleSerializer(negociacion).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_negociaciones(request):
    """
    Lista todas las negociaciones del usuario autenticado,
    tanto como comprador como productor.
    """
    # Negociaciones donde es comprador
    como_comprador = Negociacion.objects.filter(
        comprador=request.user
    ).select_related(
        'producto', 'producto__usuario', 'comprador', 'producto__municipio'
    ).prefetch_related('mensajes', 'producto__fotos')

    # Negociaciones donde es productor
    como_productor = Negociacion.objects.filter(
        producto__usuario=request.user
    ).select_related(
        'producto', 'producto__usuario', 'comprador', 'producto__municipio'
    ).prefetch_related('mensajes', 'producto__fotos')

    # Combinamos y ordenamos por última actualización
    todas = (como_comprador | como_productor).distinct().order_by('-updated_at')

    serializer = NegociacionListSerializer(
        todas,
        many=True,
        context={'request': request}
    )
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detalle_negociacion(request, negociacion_id):
    """
    Devuelve el detalle completo de una negociación con todos sus mensajes.
    Solo pueden verla el comprador o el productor del producto.
    Marca como leídos los mensajes no leídos del otro usuario.
    """
    try:
        negociacion = Negociacion.objects.select_related(
            'producto', 'producto__usuario', 'comprador'
        ).prefetch_related('mensajes__remitente').get(id=negociacion_id)
    except Negociacion.DoesNotExist:
        return Response(
            {'error': 'Negociación no encontrada.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Verifica que el usuario es parte de la negociación
    es_comprador = negociacion.comprador == request.user
    es_productor = negociacion.producto.usuario == request.user

    if not es_comprador and not es_productor:
        return Response(
            {'error': 'No tienes acceso a esta negociación.'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Marca como leídos los mensajes del otro usuario
    negociacion.mensajes.filter(
        leido=False
    ).exclude(
        remitente=request.user
    ).update(leido=True, leido_en=timezone.now())

    serializer = NegociacionDetalleSerializer(negociacion)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def enviar_mensaje(request, negociacion_id):
    """
    Envía un mensaje de texto o audio en una negociación.
    Solo pueden enviar mensajes el comprador o el productor del producto.
    No se puede enviar mensajes en negociaciones cerradas o canceladas.
    """
    try:
        negociacion = Negociacion.objects.select_related(
            'producto__usuario', 'comprador'
        ).get(id=negociacion_id)
    except Negociacion.DoesNotExist:
        return Response(
            {'error': 'Negociación no encontrada.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Verifica que el usuario es parte de la negociación
    es_comprador = negociacion.comprador == request.user
    es_productor = negociacion.producto.usuario == request.user

    if not es_comprador and not es_productor:
        return Response(
            {'error': 'No tienes acceso a esta negociación.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if negociacion.estado not in ['abierta', 'pedido_creado']:
        return Response(
            {'error': 'Esta negociación está cerrada y no acepta más mensajes.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = CrearMensajeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    tipo = serializer.validated_data['tipo']
    mensaje = None

    if tipo == 'texto':
        mensaje = Mensaje.objects.create(
            negociacion=negociacion,
            remitente=request.user,
            tipo='texto',
            contenido=serializer.validated_data['contenido']
        )

    elif tipo == 'audio':
        audio = serializer.validated_data['audio']
	# ── Validación de tipo y tamaño ──────────────────────────────────
        try:
            validar_audio(audio)
        except ValidationError as e:
            return Response({'error': e.detail}, status=status.HTTP_400_BAD_REQUEST)
        # ────────────────────────────────────────────────────────────────
        resultado = cloudinary.uploader.upload(
            audio,
            folder='agroconecta/audios',
            resource_type='video'  # Cloudinary usa 'video' para audios
        )
        mensaje = Mensaje.objects.create(
            negociacion=negociacion,
            remitente=request.user,
            tipo='audio',
            url_audio=resultado['secure_url'],
            public_id_audio=resultado['public_id']
        )

    # Actualiza la fecha de la negociación para que aparezca primero en la lista
    negociacion.save()

    # Notifica al otro participante que hay un mensaje nuevo
    if es_comprador:
        destinatario = negociacion.producto.usuario
    else:
        destinatario = negociacion.comprador

    crear_notificacion(
        usuario=destinatario,
        tipo='mensaje_nuevo',
        titulo='Mensaje nuevo',
        mensaje=f'{request.user.first_name} {request.user.last_name} te envió un mensaje sobre {negociacion.producto.nombre}.',
        url_destino=f'/negociaciones/{negociacion.id}'
    )

    return Response(
        MensajeSerializer(mensaje).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cambiar_estado_negociacion(request, negociacion_id):
    """
    El productor puede cerrar o cancelar una negociación.
    El comprador solo puede cancelarla.
    """
    try:
        negociacion = Negociacion.objects.select_related(
            'producto__usuario', 'comprador'
        ).get(id=negociacion_id)
    except Negociacion.DoesNotExist:
        return Response(
            {'error': 'Negociación no encontrada.'},
            status=status.HTTP_404_NOT_FOUND
        )

    es_comprador = negociacion.comprador == request.user
    es_productor = negociacion.producto.usuario == request.user

    if not es_comprador and not es_productor:
        return Response(
            {'error': 'No tienes acceso a esta negociación.'},
            status=status.HTTP_403_FORBIDDEN
        )

    nuevo_estado = request.data.get('estado')

    estados_validos = ['finalizada', 'cancelada']
    if nuevo_estado not in estados_validos:
        return Response(
            {'error': f'Estado inválido. Opciones: {estados_validos}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # El comprador solo puede cancelar, no finalizar
    if es_comprador and nuevo_estado == 'finalizada':
        return Response(
            {'error': 'Solo el productor puede finalizar una negociación.'},
            status=status.HTTP_403_FORBIDDEN
        )

    negociacion.estado = nuevo_estado
    negociacion.save()

    return Response(
        NegociacionDetalleSerializer(negociacion).data,
        status=status.HTTP_200_OK
    )

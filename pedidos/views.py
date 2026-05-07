from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from notificaciones.utils import crear_notificacion

from .models import Pedido, HistorialEstadoPedido, Calificacion
from .serializers import (
    PedidoListSerializer,
    PedidoDetalleSerializer,
    CrearPedidoSerializer,
    ActualizarEstadoSerializer,
    CrearCalificacionSerializer,
)
from negociacion.models import Negociacion


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_pedido(request, negociacion_id):
    """
    El productor crea un pedido desde una negociación abierta.
    Esto cierra la negociación y formaliza el acuerdo.
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

    # Solo el productor puede crear el pedido
    if negociacion.producto.usuario != request.user:
        return Response(
            {'error': 'Solo el productor puede formalizar el pedido.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if negociacion.estado != 'abierta':
        return Response(
            {'error': 'Solo se puede crear un pedido desde una negociación abierta.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verifica que no exista ya un pedido para esta negociación
    if hasattr(negociacion, 'pedido'):
        return Response(
            {'error': 'Esta negociación ya tiene un pedido asociado.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = CrearPedidoSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    datos = serializer.validated_data

    # Usamos transacción para garantizar que todo se guarda o nada se guarda
    with transaction.atomic():
        # Calcula el precio total
        precio_total = datos['cantidad_acordada'] * datos['precio_acordado']

        pedido = Pedido.objects.create(
            negociacion=negociacion,
            cantidad_acordada=datos['cantidad_acordada'],
            precio_acordado=datos['precio_acordado'],
            precio_total=precio_total,
            estado_actual='confirmado',
            direccion_entrega=datos.get('direccion_entrega', ''),
            notas_entrega=datos.get('notas_entrega', ''),
        )

        # Registra el primer estado en el historial
        HistorialEstadoPedido.objects.create(
            pedido=pedido,
            registrado_por=request.user,
            estado='confirmado',
            observacion='Pedido creado y confirmado.'
        )

        # Cierra la negociación
        negociacion.estado = 'cerrada'
        negociacion.save()

        # Notifica al comprador que su pedido fue confirmado
        crear_notificacion(
        usuario=negociacion.comprador,
        tipo='pedido_confirmado',
        titulo='Pedido confirmado',
        mensaje=f'{request.user.first_name} {request.user.last_name} confirmó tu pedido de {negociacion.producto.nombre}.',
        url_destino=f'/pedidos/{pedido.id}'
        )

    return Response(
        PedidoDetalleSerializer(pedido, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_pedidos(request):
    """
    Lista todos los pedidos del usuario autenticado,
    tanto como comprador como productor.
    """
    como_comprador = Pedido.objects.filter(
        negociacion__comprador=request.user
    ).select_related(
        'negociacion__producto',
        'negociacion__comprador',
        'negociacion__producto__usuario'
    )

    como_productor = Pedido.objects.filter(
        negociacion__producto__usuario=request.user
    ).select_related(
        'negociacion__producto',
        'negociacion__comprador',
        'negociacion__producto__usuario'
    )

    todos = (como_comprador | como_productor).distinct().order_by('-created_at')
    serializer = PedidoListSerializer(todos, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detalle_pedido(request, pedido_id):
    """
    Devuelve el detalle completo de un pedido con historial y calificaciones.
    Solo pueden verlo el comprador o el productor del pedido.
    """
    try:
        pedido = Pedido.objects.select_related(
            'negociacion__producto__usuario',
            'negociacion__comprador'
        ).prefetch_related(
            'historial_estados__registrado_por',
            'calificaciones__calificador',
            'calificaciones__calificado'
        ).get(id=pedido_id)
    except Pedido.DoesNotExist:
        return Response(
            {'error': 'Pedido no encontrado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    es_comprador = pedido.negociacion.comprador == request.user
    es_productor = pedido.negociacion.producto.usuario == request.user

    if not es_comprador and not es_productor:
        return Response(
            {'error': 'No tienes acceso a este pedido.'},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = PedidoDetalleSerializer(pedido, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def actualizar_estado(request, pedido_id):
    """
    Actualiza el estado de un pedido y registra el cambio en el historial.
    El productor puede cambiar todos los estados.
    El comprador solo puede cancelar.
    """
    try:
        pedido = Pedido.objects.select_related(
            'negociacion__producto__usuario',
            'negociacion__comprador'
        ).get(id=pedido_id)
    except Pedido.DoesNotExist:
        return Response(
            {'error': 'Pedido no encontrado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    es_comprador = pedido.negociacion.comprador == request.user
    es_productor = pedido.negociacion.producto.usuario == request.user

    if not es_comprador and not es_productor:
        return Response(
            {'error': 'No tienes acceso a este pedido.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if pedido.estado_actual in ['entregado', 'cancelado']:
        return Response(
            {'error': 'Este pedido ya está finalizado y no puede cambiar de estado.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = ActualizarEstadoSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    nuevo_estado = serializer.validated_data['estado']

    # El comprador solo puede cancelar
    if es_comprador and nuevo_estado != 'cancelado':
        return Response(
            {'error': 'Como comprador solo puedes cancelar el pedido.'},
            status=status.HTTP_403_FORBIDDEN
        )

    with transaction.atomic():
        pedido.estado_actual = nuevo_estado
        pedido.save()

        HistorialEstadoPedido.objects.create(
            pedido=pedido,
            registrado_por=request.user,
            estado=nuevo_estado,
            observacion=serializer.validated_data.get('observacion', ''),
            latitud=serializer.validated_data.get('latitud'),
            longitud=serializer.validated_data.get('longitud'),
        )

        # Determina a quién notificar según quién actualizó el estado
        if es_productor:
            destinatario = pedido.negociacion.comprador
        else:
            destinatario = pedido.negociacion.producto.usuario

        crear_notificacion(
            usuario=destinatario,
            tipo=f'pedido_{nuevo_estado}',
            titulo=f'Pedido {nuevo_estado.replace("_", " ")}',
            mensaje=f'Tu pedido de {pedido.negociacion.producto.nombre} cambió a: {nuevo_estado.replace("_", " ")}.',
            url_destino=f'/pedidos/{pedido.id}'
        )

    return Response(
        PedidoDetalleSerializer(pedido, context={'request': request}).data,
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calificar(request, pedido_id):
    """
    El comprador califica al productor y viceversa después de un pedido entregado.
    Solo se puede calificar una vez por pedido por usuario.
    Actualiza el promedio de calificaciones del usuario calificado.
    """
    try:
        pedido = Pedido.objects.select_related(
            'negociacion__producto__usuario',
            'negociacion__comprador'
        ).get(id=pedido_id)
    except Pedido.DoesNotExist:
        return Response(
            {'error': 'Pedido no encontrado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    es_comprador = pedido.negociacion.comprador == request.user
    es_productor = pedido.negociacion.producto.usuario == request.user

    if not es_comprador and not es_productor:
        return Response(
            {'error': 'No tienes acceso a este pedido.'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Solo se puede calificar después de entregar
    if pedido.estado_actual != 'entregado':
        return Response(
            {'error': 'Solo puedes calificar después de que el pedido sea entregado.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verifica que no haya calificado antes
    if pedido.calificaciones.filter(calificador=request.user).exists():
        return Response(
            {'error': 'Ya calificaste este pedido.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = CrearCalificacionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Determina a quién se califica
    if es_comprador:
        calificado = pedido.negociacion.producto.usuario
    else:
        calificado = pedido.negociacion.comprador

    with transaction.atomic():
        calificacion = Calificacion.objects.create(
            pedido=pedido,
            calificador=request.user,
            calificado=calificado,
            puntuacion=serializer.validated_data['puntuacion'],
            comentario=serializer.validated_data.get('comentario', '')
        )

        # Actualiza el promedio de calificaciones del usuario calificado
        todas_calificaciones = Calificacion.objects.filter(calificado=calificado)
        total = todas_calificaciones.count()
        promedio = sum(c.puntuacion for c in todas_calificaciones) / total

        calificado.calificacion_promedio = round(promedio, 2)
        calificado.total_calificaciones = total
        calificado.save()

        # Notifica al calificado que recibió una calificación
        crear_notificacion(
            usuario=calificado,
            tipo='calificacion_recibida',
            titulo='Nueva calificación recibida',
            mensaje=f'{request.user.first_name} {request.user.last_name} te calificó con {serializer.validated_data["puntuacion"]} estrellas.',
            url_destino=f'/pedidos/{pedido.id}'
        )

    return Response(
        {'mensaje': 'Calificación registrada exitosamente.'},
        status=status.HTTP_201_CREATED
    )
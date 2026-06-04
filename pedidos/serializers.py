from rest_framework import serializers
from .models import Pedido, HistorialEstadoPedido, Calificacion
from negociacion.models import Negociacion


class HistorialEstadoSerializer(serializers.ModelSerializer):
    """
    Serializer para el historial de estados de un pedido.
    Muestra quién registró cada cambio de estado y cuándo.
    """
    registrado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = HistorialEstadoPedido
        fields = [
            'id',
            'estado',
            'observacion',
            'latitud',
            'longitud',
            'created_at',
            'registrado_por',
            'registrado_por_nombre',
        ]
        read_only_fields = ['created_at', 'registrado_por', 'registrado_por_nombre']

    def get_registrado_por_nombre(self, obj):
        if obj.registrado_por:
            return f'{obj.registrado_por.first_name} {obj.registrado_por.last_name}'
        return None


class CalificacionSerializer(serializers.ModelSerializer):
    """
    Serializer para calificaciones.
    Valida que la puntuación esté entre 1 y 5.
    """
    calificador_nombre = serializers.SerializerMethodField()
    calificado_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Calificacion
        fields = [
            'id',
            'puntuacion',
            'comentario',
            'created_at',
            'calificador',
            'calificador_nombre',
            'calificado',
            'calificado_nombre',
        ]
        read_only_fields = [
            'created_at',
            'calificador',
            'calificador_nombre',
            'calificado',
            'calificado_nombre',
        ]

    def get_calificador_nombre(self, obj):
        return f'{obj.calificador.first_name} {obj.calificador.last_name}'

    def get_calificado_nombre(self, obj):
        return f'{obj.calificado.first_name} {obj.calificado.last_name}'

    def validate_puntuacion(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                'La puntuación debe estar entre 1 y 5.'
            )
        return value


class CrearCalificacionSerializer(serializers.Serializer):
    """
    Serializer para crear una calificación.
    """
    puntuacion = serializers.IntegerField(min_value=1, max_value=5)
    comentario = serializers.CharField(required=False, allow_blank=True)


class PedidoListSerializer(serializers.ModelSerializer):
    """
    Serializer ligero para listar pedidos.
    """
    producto_nombre = serializers.CharField(
        source='negociacion.producto.nombre',
        read_only=True
    )
    comprador_nombre = serializers.SerializerMethodField()
    productor_nombre = serializers.SerializerMethodField()
    productor_id = serializers.IntegerField(
        source='negociacion.producto.usuario.id',
        read_only=True
    )
    comprador_id = serializers.IntegerField(
        source='negociacion.comprador.id',
        read_only=True
    )

    class Meta:
        model = Pedido
        fields = [
            'id',
            'estado_actual',
            'cantidad_acordada',
            'precio_acordado',
            'precio_total',
            'producto_nombre',
            'comprador_nombre',
            'productor_nombre',
            'productor_id',
            'comprador_id',
            'created_at',
        ]

    def get_comprador_nombre(self, obj):
        comprador = obj.negociacion.comprador
        return f'{comprador.first_name} {comprador.last_name}'

    def get_productor_nombre(self, obj):
        productor = obj.negociacion.producto.usuario
        return f'{productor.first_name} {productor.last_name}'


class PedidoDetalleSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el detalle de un pedido.
    Incluye historial de estados y calificaciones.
    """
    producto_nombre = serializers.CharField(
        source='negociacion.producto.nombre',
        read_only=True
    )
    producto_id = serializers.IntegerField(
        source='negociacion.producto.id',
        read_only=True
    )
    comprador_nombre = serializers.SerializerMethodField()
    productor_nombre = serializers.SerializerMethodField()
    productor_id = serializers.IntegerField(
        source='negociacion.producto.usuario.id',
        read_only=True
    )
    comprador_id = serializers.IntegerField(
        source='negociacion.comprador.id',
        read_only=True
    )
    historial_estados = HistorialEstadoSerializer(many=True, read_only=True)
    calificaciones = CalificacionSerializer(many=True, read_only=True)
    ya_califique = serializers.SerializerMethodField()
    cancelado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = [
            'id',
            'estado_actual',
            'cantidad_acordada',
            'precio_acordado',
            'precio_total',
            'direccion_entrega',
            'notas_entrega',
            'producto_nombre',
            'producto_id',
            'comprador_nombre',
            'productor_nombre',
            'productor_id',
            'comprador_id',
            'historial_estados',
            'calificaciones',
            'ya_califique',
            'cancelado_por',
            'cancelado_por_nombre',
            'motivo_cancelacion',
            'fecha_cancelacion',
            'created_at',
            'updated_at',
        ]

    def get_comprador_nombre(self, obj):
        comprador = obj.negociacion.comprador
        return f'{comprador.first_name} {comprador.last_name}'

    def get_productor_nombre(self, obj):
        productor = obj.negociacion.producto.usuario
        return f'{productor.first_name} {productor.last_name}'

    def get_ya_califique(self, obj):
        """Indica si el usuario autenticado ya calificó este pedido."""
        request = self.context.get('request')
        if not request:
            return False
        return obj.calificaciones.filter(calificador=request.user).exists()

    def get_cancelado_por_nombre(self, obj):
        if obj.cancelado_por:
            return f'{obj.cancelado_por.first_name} {obj.cancelado_por.last_name}'
        return None


class CrearPedidoSerializer(serializers.Serializer):
    """
    Serializer para crear un pedido desde una negociación.
    El productor define los términos finales del acuerdo.
    """
    cantidad_acordada = serializers.DecimalField(max_digits=10, decimal_places=2)
    precio_acordado = serializers.DecimalField(max_digits=10, decimal_places=2)
    direccion_entrega = serializers.CharField(required=False, allow_blank=True)
    notas_entrega = serializers.CharField(required=False, allow_blank=True)

    def validate_cantidad_acordada(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'La cantidad debe ser mayor a cero.'
            )
        return value

    def validate_precio_acordado(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'El precio debe ser mayor a cero.'
            )
        return value


class ActualizarEstadoSerializer(serializers.Serializer):
    """
    Serializer para actualizar el estado de un pedido.
    """
    estado = serializers.ChoiceField(choices=[
        'pendiente',
        'confirmado',
        'preparacion',
        'en_camino',
        'entregado',
        'cancelado',
    ])
    observacion = serializers.CharField(required=False, allow_blank=True)
    latitud = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False
    )
    longitud = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False
    )
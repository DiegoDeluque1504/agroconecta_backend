from rest_framework import serializers
from .models import Negociacion, Mensaje
from usuarios.serializers import UsuarioPerfilSerializer
from productos.serializers import ProductoListSerializer


class MensajeSerializer(serializers.ModelSerializer):
    """
    Serializer para mensajes del chat de negociación.
    Incluye el nombre del remitente para mostrar en el chat.
    """
    remitente_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Mensaje
        fields = [
            'id',
            'tipo',
            'contenido',
            'url_audio',
            'leido',
            'leido_en',
            'created_at',
            'remitente',
            'remitente_nombre',
        ]
        read_only_fields = [
            'leido',
            'leido_en',
            'created_at',
            'remitente',
            'remitente_nombre',
            'url_audio',
        ]

    def get_remitente_nombre(self, obj):
        return f'{obj.remitente.first_name} {obj.remitente.last_name}'


class CrearMensajeSerializer(serializers.Serializer):
    """
    Serializer para crear un nuevo mensaje.
    Valida que el mensaje tenga contenido de texto o audio, no ambos ni ninguno.
    """
    tipo = serializers.ChoiceField(choices=['texto', 'audio'])
    contenido = serializers.CharField(required=False, allow_blank=True)
    audio = serializers.FileField(required=False)

    def validate(self, attrs):
        tipo = attrs.get('tipo')
        contenido = attrs.get('contenido')
        audio = attrs.get('audio')

        if tipo == 'texto' and not contenido:
            raise serializers.ValidationError({
                'contenido': 'El mensaje de texto no puede estar vacío.'
            })

        if tipo == 'audio' and not audio:
            raise serializers.ValidationError({
                'audio': 'Debes enviar un archivo de audio.'
            })

        return attrs


class NegociacionListSerializer(serializers.ModelSerializer):
    """
    Serializer ligero para listar negociaciones.
    Muestra el último mensaje para preview en la lista de chats.
    """
    producto_nombre = serializers.CharField(
        source='producto.nombre',
        read_only=True
    )
    producto_foto = serializers.SerializerMethodField()
    comprador_nombre = serializers.SerializerMethodField()
    productor_nombre = serializers.SerializerMethodField()
    ultimo_mensaje = serializers.SerializerMethodField()
    mensajes_no_leidos = serializers.SerializerMethodField()

    class Meta:
        model = Negociacion
        fields = [
            'id',
            'estado',
            'producto_nombre',
            'producto_foto',
            'comprador_nombre',
            'productor_nombre',
            'ultimo_mensaje',
            'mensajes_no_leidos',
            'created_at',
            'updated_at',
        ]

    def get_producto_foto(self, obj):
        foto = obj.producto.fotos.filter(es_principal=True).first()
        if foto:
            return foto.url_cloudinary
        foto = obj.producto.fotos.first()
        return foto.url_cloudinary if foto else None

    def get_comprador_nombre(self, obj):
        return f'{obj.comprador.first_name} {obj.comprador.last_name}'

    def get_productor_nombre(self, obj):
        return f'{obj.producto.usuario.first_name} {obj.producto.usuario.last_name}'

    def get_ultimo_mensaje(self, obj):
        mensaje = obj.mensajes.last()
        if not mensaje:
            return None
        if mensaje.tipo == 'audio':
            return '🎵 Audio'
        return mensaje.contenido[:50] if mensaje.contenido else None

    def get_mensajes_no_leidos(self, obj):
        usuario = self.context.get('request').user
        return obj.mensajes.filter(leido=False).exclude(remitente=usuario).count()


class NegociacionDetalleSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el detalle de una negociación con todos sus mensajes.
    """
    mensajes = MensajeSerializer(many=True, read_only=True)
    comprador_nombre = serializers.SerializerMethodField()
    productor_nombre = serializers.SerializerMethodField()
    producto_nombre = serializers.CharField(
        source='producto.nombre',
        read_only=True
    )
    producto_id = serializers.IntegerField(
        source='producto.id',
        read_only=True
    )

    class Meta:
        model = Negociacion
        fields = [
            'id',
            'estado',
            'producto_id',
            'producto_nombre',
            'comprador_nombre',
            'productor_nombre',
            'mensajes',
            'created_at',
            'updated_at',
        ]

    def get_comprador_nombre(self, obj):
        return f'{obj.comprador.first_name} {obj.comprador.last_name}'

    def get_productor_nombre(self, obj):
        return f'{obj.producto.usuario.first_name} {obj.producto.usuario.last_name}'
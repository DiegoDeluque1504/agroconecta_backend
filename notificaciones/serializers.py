from rest_framework import serializers
from .models import Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    """
    Serializer para notificaciones.
    """
    class Meta:
        model = Notificacion
        fields = [
            'id',
            'tipo',
            'titulo',
            'mensaje',
            'leida',
            'leida_en',
            'url_destino',
            'created_at',
        ]
        read_only_fields = [
            'tipo',
            'titulo',
            'mensaje',
            'leida_en',
            'url_destino',
            'created_at',
        ]
from rest_framework import serializers

# Tipos de archivo permitidos
TIPOS_IMAGEN = ['image/jpeg', 'image/png', 'image/webp']
TIPOS_AUDIO = ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/webm']

# Tamaños máximos
MAX_FOTO_MB = 5
MAX_AUDIO_MB = 10
MAX_FOTO_BYTES = MAX_FOTO_MB * 1024 * 1024    # 5MB en bytes
MAX_AUDIO_BYTES = MAX_AUDIO_MB * 1024 * 1024  # 10MB en bytes


def validar_foto(archivo):
    """
    Valida que el archivo sea una imagen JPG, PNG o WebP
    y que no supere los 5MB.
    """
    if archivo.content_type not in TIPOS_IMAGEN:
        raise serializers.ValidationError(
            f'Formato de imagen no permitido: {archivo.content_type}. '
            f'Solo se aceptan JPG, PNG o WebP.'
        )

    if archivo.size > MAX_FOTO_BYTES:
        raise serializers.ValidationError(
            f'La imagen supera el tamaño máximo de {MAX_FOTO_MB}MB. '
            f'Tu archivo pesa {round(archivo.size / 1024 / 1024, 2)}MB.'
        )


def validar_audio(archivo):
    """
    Valida que el archivo sea un audio MP3, WAV, OGG o WebM
    y que no supere los 10MB.
    """
    if archivo.content_type not in TIPOS_AUDIO:
        raise serializers.ValidationError(
            f'Formato de audio no permitido: {archivo.content_type}. '
            f'Solo se aceptan MP3, WAV, OGG o WebM.'
        )

    if archivo.size > MAX_AUDIO_BYTES:
        raise serializers.ValidationError(
            f'El audio supera el tamaño máximo de {MAX_AUDIO_MB}MB. '
            f'Tu archivo pesa {round(archivo.size / 1024 / 1024, 2)}MB.'
        )
from django.db import models
from usuarios.models import Usuario
from productos.models import Producto


class Negociacion(models.Model):
    """
    Hilo de negociación entre un comprador y un productor sobre un producto.
    Agrupa todos los mensajes del chat y tiene un estado general.
    Una negociación aceptada genera exactamente un Pedido.
    """

    class EstadoNegociacion(models.TextChoices):
        ABIERTA = 'abierta', 'Abierta'
        PEDIDO_CREADO = 'pedido_creado', 'Pedido Creado'
        FINALIZADA = 'finalizada', 'Finalizada'
        CANCELADA = 'cancelada', 'Cancelada'

    comprador = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='negociaciones_como_comprador'
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='negociaciones'
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoNegociacion.choices,
        default=EstadoNegociacion.ABIERTA
    )

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'negociacion'
        ordering = ['-created_at']
        verbose_name = 'Negociación'
        verbose_name_plural = 'Negociaciones'

    def __str__(self):
        return f'Negociación {self.id} - {self.comprador.first_name} sobre {self.producto.nombre}'


class Mensaje(models.Model):
    """
    Mensaje dentro de una negociación.
    Puede ser texto o audio almacenado en Cloudinary.
    El public_id_audio permite eliminar el audio de Cloudinary
    cuando el mensaje es borrado.
    """

    class TipoMensaje(models.TextChoices):
        TEXTO = 'texto', 'Texto'
        AUDIO = 'audio', 'Audio'

    negociacion = models.ForeignKey(
        Negociacion,
        on_delete=models.CASCADE,
        related_name='mensajes'
    )
    remitente = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='mensajes_enviados'
    )
    tipo = models.CharField(
        max_length=5,
        choices=TipoMensaje.choices,
        default=TipoMensaje.TEXTO
    )

    # Contenido: solo uno de estos dos campos tendrá valor
    contenido = models.TextField(blank=True, null=True)
    url_audio = models.URLField(max_length=500, blank=True, null=True)
    public_id_audio = models.CharField(max_length=255, blank=True, null=True)

    # Estado de lectura
    leido = models.BooleanField(default=False)
    leido_en = models.DateTimeField(blank=True, null=True)
    correo_recordatorio_enviado = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mensaje'
        ordering = ['created_at']
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'

    def __str__(self):
        return f'Mensaje de {self.remitente.first_name} en negociación {self.negociacion.id}'
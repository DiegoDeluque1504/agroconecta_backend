from django.db import models
from usuarios.models import Usuario


class Notificacion(models.Model):
    """
    Notificaciones persistentes en base de datos.
    Se generan automáticamente cuando ocurren eventos relevantes:
    mensaje nuevo, pedido aceptado, calificación recibida, etc.
    El usuario las ve cuando abre la app, sin necesidad de tiempo real.
    """

    class TipoNotificacion(models.TextChoices):
        MENSAJE_NUEVO = 'mensaje_nuevo', 'Mensaje nuevo'
        PEDIDO_CONFIRMADO = 'pedido_confirmado', 'Pedido confirmado'
        PEDIDO_EN_PREPARACION = 'pedido_en_preparacion', 'Pedido en preparación'
        PEDIDO_EN_CAMINO = 'pedido_en_camino', 'Pedido en camino'
        PEDIDO_ENTREGADO = 'pedido_entregado', 'Pedido entregado'
        PEDIDO_CANCELADO = 'pedido_cancelado', 'Pedido cancelado'
        NEGOCIACION_ACEPTADA = 'negociacion_aceptada', 'Negociación aceptada'
        NEGOCIACION_CANCELADA = 'negociacion_cancelada', 'Negociación cancelada'
        CALIFICACION_RECIBIDA = 'calificacion_recibida', 'Calificación recibida'

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )
    tipo = models.CharField(
        max_length=30,
        choices=TipoNotificacion.choices
    )
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    leida_en = models.DateTimeField(blank=True, null=True)

    # Ruta dentro de la app a la que navega el usuario al tocar la notificación
    url_destino = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notificacion'
        ordering = ['-created_at']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f'{self.tipo} para {self.usuario.first_name}'
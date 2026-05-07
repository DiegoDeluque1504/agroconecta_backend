from django.db import models
from usuarios.models import Usuario
from negociacion.models import Negociacion


class Pedido(models.Model):
    """
    Registro formal de un acuerdo cerrado entre comprador y productor.
    Nace cuando una negociación es aceptada.
    Tiene un estado actual como referencia rápida y un historial
    completo de cambios de estado en HistorialEstadoPedido.
    """

    class EstadoPedido(models.TextChoices):
        CONFIRMADO = 'confirmado', 'Confirmado'
        EN_PREPARACION = 'en_preparacion', 'En preparación'
        EN_CAMINO = 'en_camino', 'En camino'
        ENTREGADO = 'entregado', 'Entregado'
        CANCELADO = 'cancelado', 'Cancelado'

    negociacion = models.OneToOneField(
        Negociacion,
        on_delete=models.PROTECT,
        related_name='pedido'
    )

    # Términos acordados
    cantidad_acordada = models.DecimalField(max_digits=10, decimal_places=2)
    precio_acordado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Precio unitario acordado en pesos colombianos'
    )
    precio_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='cantidad_acordada * precio_acordado'
    )

    # Estado actual como referencia rápida
    estado_actual = models.CharField(
        max_length=15,
        choices=EstadoPedido.choices,
        default=EstadoPedido.CONFIRMADO
    )

    # Información de entrega
    direccion_entrega = models.CharField(max_length=500, blank=True, null=True)
    notas_entrega = models.TextField(blank=True, null=True)

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pedido'
        ordering = ['-created_at']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    def __str__(self):
        return f'Pedido {self.id} - {self.estado_actual}'


class HistorialEstadoPedido(models.Model):
    """
    Registro de cada cambio de estado de un pedido.
    En lugar de sobrescribir el estado, cada cambio genera un registro
    nuevo con fecha, quién lo registró y coordenadas GPS opcionales.
    """

    class EstadoPedido(models.TextChoices):
        CONFIRMADO = 'confirmado', 'Confirmado'
        EN_PREPARACION = 'en_preparacion', 'En preparación'
        EN_CAMINO = 'en_camino', 'En camino'
        ENTREGADO = 'entregado', 'Entregado'
        CANCELADO = 'cancelado', 'Cancelado'

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='historial_estados'
    )
    registrado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='estados_registrados'
    )
    estado = models.CharField(
        max_length=15,
        choices=EstadoPedido.choices
    )
    observacion = models.TextField(blank=True, null=True)

    # Ubicación GPS opcional al momento de registrar el estado
    latitud = models.DecimalField(
        max_digits=9, decimal_places=6,
        blank=True, null=True
    )
    longitud = models.DecimalField(
        max_digits=9, decimal_places=6,
        blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historial_estado_pedido'
        ordering = ['created_at']
        verbose_name = 'Historial de estado de pedido'
        verbose_name_plural = 'Historial de estados de pedidos'

    def __str__(self):
        return f'Pedido {self.pedido.id} -> {self.estado}'


class Calificacion(models.Model):
    """
    Calificación mutua entre comprador y productor después de un pedido entregado.
    Ambas partes pueden calificarse. El sistema valida que solo se pueda
    calificar una vez por rol por pedido.
    """
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='calificaciones'
    )
    calificador = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='calificaciones_emitidas'
    )
    calificado = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='calificaciones_recibidas'
    )
    puntuacion = models.PositiveSmallIntegerField(
        help_text='Puntuación del 1 al 5'
    )
    comentario = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'calificacion'
        # Garantiza que cada usuario solo pueda calificar una vez por pedido
        unique_together = [['pedido', 'calificador']]
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'

    def __str__(self):
        return f'{self.calificador.first_name} calificó a {self.calificado.first_name} con {self.puntuacion} estrellas'
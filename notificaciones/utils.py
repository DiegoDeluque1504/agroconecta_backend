from .models import Notificacion


def crear_notificacion(usuario, tipo, titulo, mensaje, url_destino=None):
    """
    Función utilitaria para crear notificaciones desde cualquier módulo.
    Se llama desde pedidos, negociaciones y calificaciones.

    Uso:
        from notificaciones.utils import crear_notificacion
        crear_notificacion(
            usuario=comprador,
            tipo='pedido_confirmado',
            titulo='Tu pedido fue confirmado',
            mensaje='Diego De Luque confirmó tu pedido de Mango Tommy',
            url_destino='/pedidos/1'
        )
    """
    Notificacion.objects.create(
        usuario=usuario,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        url_destino=url_destino
    )
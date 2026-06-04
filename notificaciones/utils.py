import logging

from usuarios.email_service import enviar_correo_en_segundo_plano, enviar_correo_notificacion

from .models import Notificacion

logger = logging.getLogger(__name__)


def crear_notificacion(usuario, tipo, titulo, mensaje, url_destino=None):
    """
    Crea una notificación in-app y envía el mismo aviso por correo (Resend) en segundo plano.
    """
    Notificacion.objects.create(
        usuario=usuario,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        url_destino=url_destino,
    )

    enviar_correo_en_segundo_plano(
        enviar_correo_notificacion,
        destinatario=usuario.email,
        nombre=usuario.first_name,
        titulo=titulo,
        mensaje=mensaje,
        url_destino=url_destino,
    )

from datetime import timedelta

from django.utils import timezone

from negociacion.models import Mensaje
from usuarios.email_service import enviar_correo_recordatorio


def procesar_recordatorios_mensajes():
    """
    Envía correos consolidados de mensajes no leídos con más de 10 minutos.
    Retorna estadísticas para logs o respuesta HTTP.
    """
    diez_minutos_atras = timezone.now() - timedelta(minutes=10)

    mensajes_pendientes = Mensaje.objects.filter(
        leido=False,
        created_at__lte=diez_minutos_atras,
        correo_recordatorio_enviado=False,
    ).select_related(
        'negociacion',
        'remitente',
        'negociacion__comprador',
        'negociacion__producto__usuario',
    )

    if not mensajes_pendientes.exists():
        return {'enviados': 0, 'fallidos': 0, 'mensaje': 'No hay mensajes pendientes por notificar.'}

    por_destinatario = {}
    for msg in mensajes_pendientes:
        if msg.remitente == msg.negociacion.comprador:
            destinatario = msg.negociacion.producto.usuario
        else:
            destinatario = msg.negociacion.comprador

        if destinatario.id not in por_destinatario:
            por_destinatario[destinatario.id] = {
                'usuario': destinatario,
                'mensajes': [],
            }
        por_destinatario[destinatario.id]['mensajes'].append(msg)

    enviados = 0
    fallidos = 0

    for info in por_destinatario.values():
        usuario = info['usuario']
        mensajes = info['mensajes']

        resumen_chats = {}
        for msg in mensajes:
            clave = (msg.remitente.first_name, msg.negociacion.producto.nombre)
            resumen_chats[clave] = resumen_chats.get(clave, 0) + 1

        detalles_html = '<ul>'
        for (remitente_nombre, producto_nombre), cant in resumen_chats.items():
            detalles_html += (
                f'<li><strong>{remitente_nombre}</strong>: {cant} mensaje(s) '
                f"nuevo(s) sobre '{producto_nombre}'</li>"
            )
        detalles_html += '</ul>'

        resultado = enviar_correo_recordatorio(
            usuario.email,
            usuario.first_name,
            detalles_html,
        )

        if resultado is not None:
            enviados += 1
            Mensaje.objects.filter(id__in=[m.id for m in mensajes]).update(
                correo_recordatorio_enviado=True
            )
        else:
            fallidos += 1

    return {
        'enviados': enviados,
        'fallidos': fallidos,
        'mensaje': f'Procesados {enviados + fallidos} destinatario(s).',
    }

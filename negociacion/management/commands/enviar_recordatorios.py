from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import requests
import logging

from negociacion.models import Mensaje

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Envía un recordatorio por correo electrónico para mensajes no leídos después de 10 minutos.'

    def handle(self, *args, **options):
        # Hace 10 minutos
        diez_minutos_atras = timezone.now() - timedelta(minutes=10)
        
        # Buscar mensajes:
        # - No leídos
        # - Creados hace más de 10 minutos
        # - Que no tengan recordatorio enviado
        mensajes_pendientes = Mensaje.objects.filter(
            leido=False,
            created_at__lte=diez_minutos_atras,
            correo_recordatorio_enviado=False
        ).select_related('negociacion', 'remitente', 'negociacion__comprador', 'negociacion__producto__usuario')
        
        if not mensajes_pendientes.exists():
            self.stdout.write("No hay mensajes pendientes por notificar.")
            return

        # Agrupar por destinatario para enviar un solo correo por destinatario
        por_destinatario = {}
        for msg in mensajes_pendientes:
            # Quién es el destinatario?
            if msg.remitente == msg.negociacion.comprador:
                destinatario = msg.negociacion.producto.usuario
            else:
                destinatario = msg.negociacion.comprador
                
            if destinatario.id not in por_destinatario:
                por_destinatario[destinatario.id] = {
                    'usuario': destinatario,
                    'mensajes': []
                }
            por_destinatario[destinatario.id]['mensajes'].append(msg)
            
        api_key = settings.RESEND_API_KEY
        from_email = settings.DEFAULT_FROM_EMAIL
        
        for dest_id, info in por_destinatario.items():
            usuario = info['usuario']
            mensajes = info['mensajes']
            
            # Crear lista de remitentes y productos para el correo
            resumen_chats = {}
            for msg in mensajes:
                clave = (msg.remitente.first_name, msg.negociacion.producto.nombre)
                resumen_chats[clave] = resumen_chats.get(clave, 0) + 1
                
            detalles_html = "<ul>"
            for (remitente_nombre, producto_nombre), cant in resumen_chats.items():
                detalles_html += f"<li><strong>{remitente_nombre}</strong>: {cant} mensaje(s) nuevo(s) sobre el producto '{producto_nombre}'</li>"
            detalles_html += "</ul>"
            
            self.stdout.write(f"Preparando correo para {usuario.email}...")
            
            if not api_key:
                logger.warning(f"[DEV] RESEND_API_KEY no configurada. Saltando envío de correo de recordatorio a {usuario.email}")
                # En desarrollo, los marcamos como enviados para no saturar los logs
                Mensaje.objects.filter(id__in=[m.id for m in mensajes]).update(correo_recordatorio_enviado=True)
                continue
                
            payload = {
                'from': from_email,
                'to': [usuario.email],
                'subject': 'Tienes nuevos mensajes pendientes en AgroConecta',
                'html': f'''
                <h2>Hola {usuario.first_name},</h2>
                <p>Tienes mensajes sin leer en <strong>AgroConecta</strong> recibidos hace más de 10 minutos:</p>
                {detalles_html}
                <p>Ingresa a la aplicación para responderles y continuar con tus negociaciones.</p>
                <p><a href="{settings.FRONTEND_URL}/negociaciones">Ir a mis negociaciones</a></p>
                <br>
                <p>El equipo de AgroConecta</p>
                ''',
            }
            
            try:
                response = requests.post(
                    'https://api.resend.com/emails',
                    json=payload,
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json',
                    },
                    timeout=15,
                )
                if response.status_code < 400:
                    self.stdout.write(self.style.SUCCESS(f"Correo de recordatorio enviado exitosamente a {usuario.email}"))
                    # Marcar los mensajes como notificados
                    Mensaje.objects.filter(id__in=[m.id for m in mensajes]).update(correo_recordatorio_enviado=True)
                else:
                    self.stdout.write(self.style.ERROR(f"Error al enviar a {usuario.email} (Código {response.status_code}): {response.text}"))
            except requests.RequestException:
                logger.exception(f"Error de red al conectar con la API de Resend para recordatorio de {usuario.email}")

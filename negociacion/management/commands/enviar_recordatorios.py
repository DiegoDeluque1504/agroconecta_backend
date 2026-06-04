from django.core.management.base import BaseCommand

from negociacion.recordatorios import procesar_recordatorios_mensajes


class Command(BaseCommand):
    help = 'Envía recordatorio por correo de mensajes no leídos (10+ min sin leer).'

    def handle(self, *args, **options):
        resultado = procesar_recordatorios_mensajes()
        self.stdout.write(resultado['mensaje'])
        if resultado['enviados']:
            self.stdout.write(self.style.SUCCESS(f"Enviados: {resultado['enviados']}"))
        if resultado['fallidos']:
            self.stdout.write(self.style.ERROR(f"Fallidos: {resultado['fallidos']}"))

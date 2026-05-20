from django.core.management.base import BaseCommand
from django.utils import timezone

from usuarios.models import TokenVerificacion


class Command(BaseCommand):
    help = 'Elimina tokens de verificación de correo que han expirado y nunca fueron usados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la eliminación sin borrar realmente los tokens',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        expired_tokens = TokenVerificacion.objects.filter(
            expira_en__lt=timezone.now(),
            usado=False,
        )

        count = expired_tokens.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No hay tokens expirados para eliminar.')
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY RUN] Se eliminarían {count} tokens expirados.'
                )
            )
        else:
            expired_tokens.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Se eliminaron {count} tokens expirados correctamente.'
                )
            )

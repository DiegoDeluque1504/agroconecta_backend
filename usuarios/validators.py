from django.core.exceptions import ValidationError
import re

class AgroConectaPasswordValidator:
    """
    Validador personalizado de contraseñas de Django para exigir:
    - Mínimo 8 caracteres
    - Al menos una letra
    - Al menos un número
    """
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(
                "La contraseña debe tener un mínimo de 8 caracteres.",
                code='password_too_short',
            )
        if not re.search(r'[a-zA-Z]', password):
            raise ValidationError(
                "La contraseña debe contener al menos una letra.",
                code='password_no_letters',
            )
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                "La contraseña debe contener al menos un número.",
                code='password_no_numbers',
            )

    def get_help_text(self):
        return "Tu contraseña debe tener al menos 8 caracteres y contener una combinación de letras y números."

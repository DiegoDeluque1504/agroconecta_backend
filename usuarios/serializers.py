from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Usuario, Municipio, TokenVerificacion


class MunicipioSerializer(serializers.ModelSerializer):
    """
    Serializer para listar municipios.
    Se usa en el formulario de registro para que el usuario elija su municipio.
    """
    class Meta:
        model = Municipio
        fields = ['id', 'nombre', 'codigo_dane']


class RegistroSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro de nuevos usuarios.
    Valida que las contraseñas coincidan y que el correo no exista ya.
    """
    # Campo de confirmación de contraseña, solo para validación, no se guarda
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        label='Confirmar contraseña'
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        label='Contraseña'
    )

    class Meta:
        model = Usuario
        fields = [
            'first_name',
            'last_name',
            'email',
            'telefono',
            'password',
            'password2',
            'es_productor',
            'es_comprador',
            'municipio',
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        """Valida que las dos contraseñas coincidan."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                'password': 'Las contraseñas no coinciden.'
            })

        # Valida que el usuario tenga al menos un rol seleccionado
        if not attrs.get('es_productor') and not attrs.get('es_comprador'):
            raise serializers.ValidationError({
                'roles': 'Debe seleccionar al menos un rol: productor o comprador.'
            })

        return attrs

    def create(self, validated_data):
        """Crea el usuario con la contraseña encriptada y la cuenta inactiva."""
        # Removemos password2 porque no es un campo del modelo
        validated_data.pop('password2')
        password = validated_data.pop('password')

        # Generamos el username a partir del email para cumplir con AbstractUser
        email = validated_data.get('email')
        validated_data['username'] = email

        # La cuenta empieza inactiva hasta que verifique el correo
        validated_data['is_active'] = False
        validated_data['email_verificado'] = False

        usuario = Usuario.objects.create(**validated_data)
        usuario.set_password(password)
        usuario.save()

        return usuario


class UsuarioPerfilSerializer(serializers.ModelSerializer):
    municipio_detalle = MunicipioSerializer(
        source='municipio',
        read_only=True
    )

    class Meta:
        model = Usuario
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'telefono',
            'es_productor',
            'es_comprador',
            'email_verificado',
            'latitud',
            'longitud',
            'calificacion_promedio',
            'total_calificaciones',
            'municipio',
            'municipio_detalle',
            'created_at',
        ]
        read_only_fields = [
            'email',
            'email_verificado',
            'calificacion_promedio',
            'total_calificaciones',
            'created_at',
        ]

    # ── Validaciones de coordenadas GPS ──────────────────────────────────

    def validate_latitud(self, value):
        """Valida que la latitud esté dentro del rango geográfico válido."""
        if value is not None:
            if value < -90 or value > 90:
                raise serializers.ValidationError(
                    'La latitud debe estar entre -90 y 90.'
                )
        return value

    def validate_longitud(self, value):
        """Valida que la longitud esté dentro del rango geográfico válido."""
        if value is not None:
            if value < -180 or value > 180:
                raise serializers.ValidationError(
                    'La longitud debe estar entre -180 y 180.'
                )
        return value

    def validate(self, attrs):
        """
        Valida que las coordenadas correspondan al departamento de La Guajira.
        Bounding box oficial del departamento según el IGAC:
          Latitud:  10.38° N  a  12.47° N
          Longitud: 71.12° O  a  73.39° O
        """
        latitud = attrs.get('latitud')
        longitud = attrs.get('longitud')

        # Solo valida si el usuario está enviando coordenadas
        if latitud is not None and longitud is not None:
            LAT_MIN, LAT_MAX = 10.38, 12.47
            LON_MIN, LON_MAX = -73.39, -71.12

            if not (LAT_MIN <= float(latitud) <= LAT_MAX):
                raise serializers.ValidationError({
                    'latitud': (
                        f'La latitud {latitud} no corresponde a La Guajira. '
                        f'Debe estar entre {LAT_MIN} y {LAT_MAX}.'
                    )
                })

            if not (LON_MIN <= float(longitud) <= LON_MAX):
                raise serializers.ValidationError({
                    'longitud': (
                        f'La longitud {longitud} no corresponde a La Guajira. '
                        f'Debe estar entre {LON_MIN} y {LON_MAX}.'
                    )
                })

        return attrs


class VerificacionEmailSerializer(serializers.Serializer):
    """
    Serializer para verificar el correo con el token recibido.
    """
    token = serializers.CharField(required=True)


class LoginSerializer(serializers.Serializer):
    """
    Serializer para el login. Solo valida que los campos estén presentes,
    la autenticación real la maneja la vista.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class CambiarPasswordSerializer(serializers.Serializer):
    """
    Serializer para cambiar la contraseña del usuario autenticado.
    Valida la contraseña actual y aplica las reglas de Django para la nueva.
    """
    password_actual = serializers.CharField(
        required=True,
        write_only=True,
        label='Contraseña actual',
    )
    password_nueva = serializers.CharField(
        required=True,
        write_only=True,
        label='Contraseña nueva',
    )

    def validate(self, attrs):
        usuario = self.context['request'].user

        if not usuario.check_password(attrs['password_actual']):
            raise serializers.ValidationError({
                'password_actual': 'La contraseña actual es incorrecta.',
            })

        if attrs['password_actual'] == attrs['password_nueva']:
            raise serializers.ValidationError({
                'password_nueva': 'La nueva contraseña debe ser diferente a la actual.',
            })

        validate_password(attrs['password_nueva'], user=usuario)
        return attrs

class SolicitarRecuperacionSerializer(serializers.Serializer):
    """
    Serializer para solicitar el restablecimiento de contrasena.
    Solo valida que el email sea un email valido.
    """
    email = serializers.EmailField(required=True)


class ResetPasswordSerializer(serializers.Serializer):
    """
    Serializer para confirmar el restablecimiento de contrasena.
    Valida el token UUID y la nueva contrasena con las reglas de Django.
    """
    token = serializers.UUIDField(required=True)
    password_nueva = serializers.CharField(
        required=True,
        write_only=True,
        label='Nueva contrasena',
    )

    def validate_password_nueva(self, value):
        validate_password(value)
        return value

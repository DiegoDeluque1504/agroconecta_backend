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
    """
    Serializer para ver y editar el perfil del usuario autenticado.
    No expone la contraseña ni datos sensibles.
    """
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
        # Estos campos no se pueden editar directamente
        read_only_fields = [
            'email',
            'email_verificado',
            'calificacion_promedio',
            'total_calificaciones',
            'created_at',
        ]


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
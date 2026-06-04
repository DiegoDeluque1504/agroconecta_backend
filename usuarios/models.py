from django.contrib.auth.models import AbstractUser
from django.db import models


class Municipio(models.Model):
    """
    Tabla de referencia con los 15 municipios oficiales de La Guajira.
    Se precarga con datos fijos, los usuarios no pueden crear municipios nuevos.
    """
    nombre = models.CharField(max_length=100)
    codigo_dane = models.CharField(max_length=10, unique=True)

    class Meta:
        db_table = 'municipio'
        ordering = ['nombre']
        verbose_name = 'Municipio'
        verbose_name_plural = 'Municipios'

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser.
    Un usuario puede ser productor, comprador, o ambos simultáneamente.
    """

    # Roles: un usuario puede tener ambos roles al mismo tiempo
    es_productor = models.BooleanField(default=False)
    es_comprador = models.BooleanField(default=False)
    
    email = models.EmailField(unique=True)

    # Datos de contacto
    telefono = models.CharField(max_length=20, blank=True, null=True)

    # Verificación de correo electrónico
    email_verificado = models.BooleanField(default=False)

    # Geolocalización del productor
    # DecimalField con 9 dígitos y 6 decimales da precisión de centímetros
    latitud = models.DecimalField(
        max_digits=9, decimal_places=6,
        blank=True, null=True
    )
    longitud = models.DecimalField(
        max_digits=9, decimal_places=6,
        blank=True, null=True
    )

    # Reputación: se actualiza cada vez que llega una calificación nueva
    calificacion_promedio = models.DecimalField(
        max_digits=3, decimal_places=2,
        default=0.00
    )
    total_calificaciones = models.IntegerField(default=0)

    # Municipio de residencia
    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios'
    )

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Django usa el email como identificador principal en lugar del username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.email})'


class TokenVerificacion(models.Model):
    """
    Token temporal para verificar el correo electrónico del usuario.
    Tiene fecha de expiración y se marca como usado una vez consumido.
    """

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='token_verificacion'
    )
    token = models.CharField(max_length=255, unique=True)
    expira_en = models.DateTimeField()
    usado = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'token_verificacion'
        verbose_name = 'Token de verificación'
        verbose_name_plural = 'Tokens de verificación'

    def __str__(self):
        return f'Token de {self.usuario.email}'


class DispositivoConfiable(models.Model):
    """
    Registra los dispositivos desde los cuales el usuario ha iniciado sesión.
    Se utiliza para detectar accesos sospechosos o desde dispositivos nuevos.
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='dispositivos_confiables'
    )
    user_agent = models.TextField()
    ip = models.GenericIPAddressField(blank=True, null=True)
    navegador = models.CharField(max_length=50, blank=True, null=True)
    sistema_operativo = models.CharField(max_length=50, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ultimo_acceso = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dispositivo_confiable'
        unique_together = [['usuario', 'user_agent']]
        verbose_name = 'Dispositivo Confiable'
        verbose_name_plural = 'Dispositivos Confiables'

    def __str__(self):
        return f'{self.navegador} en {self.sistema_operativo} ({self.usuario.email})'
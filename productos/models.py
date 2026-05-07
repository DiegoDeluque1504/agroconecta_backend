from django.db import models
from usuarios.models import Usuario, Municipio


class CategoriaProducto(models.Model):
    """
    Tabla de referencia con categorías fijas de productos agrícolas.
    Se precarga con datos fijos, los usuarios no pueden crear categorías nuevas.
    """
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    icono = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Nombre del icono para mostrar en la interfaz'
    )

    class Meta:
        db_table = 'categoria_producto'
        ordering = ['nombre']
        verbose_name = 'Categoría de producto'
        verbose_name_plural = 'Categorías de productos'

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """
    Producto agrícola publicado por un productor.
    Referencia al municipio donde está disponible el producto,
    que puede ser diferente al municipio del productor.
    """

    class UnidadMedida(models.TextChoices):
        KILOGRAMO = 'kg', 'Kilogramo'
        LIBRA = 'lb', 'Libra'
        UNIDAD = 'und', 'Unidad'
        BULTO = 'bulto', 'Bulto'
        LITRO = 'lt', 'Litro'
        ARROBA = 'arroba', 'Arroba'

    class EstadoProducto(models.TextChoices):
        ACTIVO = 'activo', 'Activo'
        AGOTADO = 'agotado', 'Agotado'
        INACTIVO = 'inactivo', 'Inactivo'

    # Información básica
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Precio en pesos colombianos'
    )
    cantidad_disponible = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    unidad_medida = models.CharField(
        max_length=10,
        choices=UnidadMedida.choices,
        default=UnidadMedida.KILOGRAMO
    )
    estado = models.CharField(
        max_length=10,
        choices=EstadoProducto.choices,
        default=EstadoProducto.ACTIVO
    )

    # Relaciones
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='productos'
    )
    categoria = models.ForeignKey(
        CategoriaProducto,
        on_delete=models.PROTECT,
        related_name='productos'
    )
    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.PROTECT,
        related_name='productos'
    )

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'producto'
        ordering = ['-created_at']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return f'{self.nombre} - {self.usuario.first_name}'


class FotoProducto(models.Model):
    """
    Fotos de un producto almacenadas en Cloudinary.
    Un producto puede tener varias fotos pero solo una principal.
    Se guarda el public_id para poder eliminar la imagen de Cloudinary
    cuando el productor la borre desde la app.
    """
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='fotos'
    )
    url_cloudinary = models.URLField(max_length=500)
    public_id_cloudinary = models.CharField(max_length=255)
    es_principal = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'foto_producto'
        ordering = ['orden']
        verbose_name = 'Foto de producto'
        verbose_name_plural = 'Fotos de productos'

    def __str__(self):
        return f'Foto de {self.producto.nombre}'
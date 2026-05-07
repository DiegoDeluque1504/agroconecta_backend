from rest_framework import serializers
from .models import Producto, FotoProducto, CategoriaProducto
from usuarios.serializers import MunicipioSerializer


class CategoriaProductoSerializer(serializers.ModelSerializer):
    """Serializer para listar categorías de productos."""
    class Meta:
        model = CategoriaProducto
        fields = ['id', 'nombre', 'descripcion', 'icono']


class FotoProductoSerializer(serializers.ModelSerializer):
    """Serializer para las fotos de un producto."""
    class Meta:
        model = FotoProducto
        fields = [
            'id',
            'url_cloudinary',
            'public_id_cloudinary',
            'es_principal',
            'orden',
        ]
        # El productor no envía estos campos, los genera el backend
        read_only_fields = ['url_cloudinary', 'public_id_cloudinary']


class ProductoListSerializer(serializers.ModelSerializer):
    """
    Serializer ligero para el catálogo.
    Solo devuelve los campos necesarios para mostrar la tarjeta del producto.
    Optimizado para conexiones lentas: mínimo de datos.
    """
    categoria_nombre = serializers.CharField(
        source='categoria.nombre',
        read_only=True
    )
    municipio_nombre = serializers.CharField(
        source='municipio.nombre',
        read_only=True
    )
    productor_nombre = serializers.SerializerMethodField()
    foto_principal = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            'id',
            'nombre',
            'precio',
            'cantidad_disponible',
            'unidad_medida',
            'estado',
            'categoria_nombre',
            'municipio_nombre',
            'productor_nombre',
            'foto_principal',
        ]

    def get_productor_nombre(self, obj):
        return f'{obj.usuario.first_name} {obj.usuario.last_name}'

    def get_foto_principal(self, obj):
        foto = obj.fotos.filter(es_principal=True).first()
        if foto:
            return foto.url_cloudinary
        # Si no hay foto principal, devuelve la primera foto disponible
        foto = obj.fotos.first()
        return foto.url_cloudinary if foto else None


class ProductoDetalleSerializer(serializers.ModelSerializer):
    """
    Serializer completo para el detalle de un producto.
    Incluye todas las fotos y datos del productor.
    """
    categoria = CategoriaProductoSerializer(read_only=True)
    municipio = MunicipioSerializer(read_only=True)
    fotos = FotoProductoSerializer(many=True, read_only=True)
    productor = serializers.SerializerMethodField()

    # Campos de escritura para crear/editar
    categoria_id = serializers.IntegerField(write_only=True)
    municipio_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Producto
        fields = [
            'id',
            'nombre',
            'descripcion',
            'precio',
            'cantidad_disponible',
            'unidad_medida',
            'estado',
            'categoria',
            'categoria_id',
            'municipio',
            'municipio_id',
            'fotos',
            'productor',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_productor(self, obj):
        return {
            'id': obj.usuario.id,
            'nombre': f'{obj.usuario.first_name} {obj.usuario.last_name}',
            'municipio': obj.usuario.municipio.nombre if obj.usuario.municipio else None,
            'calificacion_promedio': obj.usuario.calificacion_promedio,
            'total_calificaciones': obj.usuario.total_calificaciones,
            'latitud': obj.usuario.latitud,
            'longitud': obj.usuario.longitud,
        }
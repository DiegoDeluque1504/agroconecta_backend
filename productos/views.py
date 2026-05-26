from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework import serializers
from django.db.models import Q
from file_validators import validar_foto  # CORREGIDO: era 'from validators import ...'
import cloudinary.uploader

from .models import Producto, FotoProducto, CategoriaProducto
from .serializers import (
    ProductoListSerializer,
    ProductoDetalleSerializer,
    CategoriaProductoSerializer,
    FotoProductoSerializer,
)
from .permissions import EsProductor


@api_view(['GET'])
@permission_classes([AllowAny])
def listar_categorias(request):
    """
    Endpoint público para listar todas las categorías de productos.
    Se usa en los filtros del catálogo y en el formulario de publicación.
    """
    categorias = CategoriaProducto.objects.all()
    serializer = CategoriaProductoSerializer(categorias, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def catalogo(request):
    """
    Endpoint público del catálogo de productos.
    Soporta filtros por categoría, municipio y rango de precio.
    Soporta búsqueda por nombre o descripción.
    Optimizado para conexiones lentas: devuelve solo los campos necesarios.
    """
    productos = Producto.objects.filter(
        estado='activo'
    ).select_related(
        'categoria', 'municipio', 'usuario','usuario__municipio'
    ).prefetch_related('fotos')

    # Filtro por categoría
    categoria_id = request.query_params.get('categoria')
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    # Filtro por municipio
    municipio_id = request.query_params.get('municipio')
    if municipio_id:
        productos = productos.filter(municipio_id=municipio_id)

    # Filtro por rango de precio
    precio_min = request.query_params.get('precio_min')
    precio_max = request.query_params.get('precio_max')
    if precio_min:
        productos = productos.filter(precio__gte=precio_min)
    if precio_max:
        productos = productos.filter(precio__lte=precio_max)

    # Búsqueda por nombre o descripción
    busqueda = request.query_params.get('busqueda')
    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) |
            Q(descripcion__icontains=busqueda)
        )

    # Paginación
    paginator = PageNumberPagination()
    paginator.page_size = 12
    resultado = paginator.paginate_queryset(productos, request)
    serializer = ProductoListSerializer(resultado, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def detalle_producto(request, producto_id):
    """
    Endpoint público para ver el detalle completo de un producto.
    Incluye todas las fotos y datos del productor.
    """
    try:
        producto = Producto.objects.select_related(
            'categoria', 'municipio', 'usuario__municipio'
        ).prefetch_related('fotos').get(id=producto_id)
    except Producto.DoesNotExist:
        return Response(
            {'error': 'Producto no encontrado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = ProductoDetalleSerializer(producto)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, EsProductor])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def crear_producto(request):
    """
    Endpoint para que un productor publique un nuevo producto.
    Acepta datos del producto y opcionalmente una foto principal.
    """
    serializer = ProductoDetalleSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    producto = serializer.save(usuario=request.user)

    foto = request.FILES.get('foto')
    if foto:
        # Validación de tipo y tamaño
        try:
            validar_foto(foto)
        except serializers.ValidationError as e:
            return Response({'error': e.detail}, status=status.HTTP_400_BAD_REQUEST)

        resultado = cloudinary.uploader.upload(
            foto,
            folder='agroconecta/productos',
            resource_type='image'
        )
        FotoProducto.objects.create(
            producto=producto,
            url_cloudinary=resultado['secure_url'],
            public_id_cloudinary=resultado['public_id'],
            es_principal=True,
            orden=0
        )

    producto.refresh_from_db()
    return Response(
        ProductoDetalleSerializer(producto).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, EsProductor])
def gestionar_producto(request, producto_id):
    """
    Endpoint para editar o eliminar un producto.
    Solo el productor dueño del producto puede modificarlo o eliminarlo.
    """
    try:
        producto = Producto.objects.get(id=producto_id)
    except Producto.DoesNotExist:
        return Response(
            {'error': 'Producto no encontrado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if producto.usuario != request.user:
        return Response(
            {'error': 'No tienes permiso para modificar este producto.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if request.method == 'DELETE':
        from django.db.models import ProtectedError
        try:
            # Guardamos las referencias a las fotos antes de borrar de la base de datos
            fotos_a_eliminar = list(producto.fotos.all())
            
            # Intentamos eliminar el producto de la base de datos.
            # Si tiene pedidos o referencias protegidas, lanzará ProtectedError y no se borrará nada.
            producto.delete()
            
            # Si la eliminación en BD fue exitosa, procedemos a borrar de Cloudinary
            for foto in fotos_a_eliminar:
                cloudinary.uploader.destroy(foto.public_id_cloudinary)
                
            return Response(
                {'mensaje': 'Producto eliminado correctamente.'},
                status=status.HTTP_200_OK
            )
        except ProtectedError:
            return Response(
                {
                    'error': (
                        'No se puede eliminar este producto porque está asociado a pedidos o negociaciones en curso. '
                        'Te sugerimos cambiar su estado a "Inactivo" para que no aparezca en el catálogo público.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    if request.method in ['PUT', 'PATCH']:
        serializer = ProductoDetalleSerializer(
            producto,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated, EsProductor])
@parser_classes([MultiPartParser, FormParser])
def agregar_foto(request, producto_id):
    """
    Endpoint para agregar fotos adicionales a un producto existente.
    El productor puede subir una foto a la vez.
    """
    try:
        producto = Producto.objects.get(id=producto_id, usuario=request.user)
    except Producto.DoesNotExist:
        return Response(
            {'error': 'Producto no encontrado o no tienes permiso.'},
            status=status.HTTP_404_NOT_FOUND
        )

    foto = request.FILES.get('foto')
    if not foto:
        return Response(
            {'error': 'No se envió ninguna foto.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validación de tipo y tamaño
    try:
        validar_foto(foto)
    except serializers.ValidationError as e:
        return Response({'error': e.detail}, status=status.HTTP_400_BAD_REQUEST)

    resultado = cloudinary.uploader.upload(
        foto,
        folder='agroconecta/productos',
        resource_type='image'
    )

    ultimo_orden = producto.fotos.count()
    es_principal = ultimo_orden == 0

    foto_obj = FotoProducto.objects.create(
        producto=producto,
        url_cloudinary=resultado['secure_url'],
        public_id_cloudinary=resultado['public_id'],
        es_principal=es_principal,
        orden=ultimo_orden
    )

    return Response(
        FotoProductoSerializer(foto_obj).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, EsProductor])
def eliminar_foto(request, foto_id):
    """
    Endpoint para eliminar una foto de un producto.
    Elimina la foto tanto de la base de datos como de Cloudinary.
    """
    try:
        foto = FotoProducto.objects.get(
            id=foto_id,
            producto__usuario=request.user
        )
    except FotoProducto.DoesNotExist:
        return Response(
            {'error': 'Foto no encontrada o no tienes permiso.'},
            status=status.HTTP_404_NOT_FOUND
        )

    cloudinary.uploader.destroy(foto.public_id_cloudinary)

    era_principal = foto.es_principal
    producto = foto.producto
    foto.delete()

    if era_principal:
        siguiente_foto = producto.fotos.first()
        if siguiente_foto:
            siguiente_foto.es_principal = True
            siguiente_foto.save()

    return Response(
        {'mensaje': 'Foto eliminada correctamente.'},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_productos(request):
    """
    Endpoint para que el productor vea sus propios productos.
    Incluye todos los estados, no solo los activos.
    """
    productos = Producto.objects.filter(
        usuario=request.user
    ).select_related(
        'categoria', 'municipio'
    ).prefetch_related('fotos')

    serializer = ProductoListSerializer(productos, many=True)
    return Response(serializer.data)
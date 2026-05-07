from django.urls import path
from . import views

urlpatterns = [
    # Endpoints públicos
    path('categorias/', views.listar_categorias, name='listar-categorias'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('<int:producto_id>/', views.detalle_producto, name='detalle-producto'),

    # Endpoints protegidos para productores
    path('crear/', views.crear_producto, name='crear-producto'),
    path('<int:producto_id>/gestionar/', views.gestionar_producto, name='gestionar-producto'),
    path('<int:producto_id>/fotos/agregar/', views.agregar_foto, name='agregar-foto'),
    path('fotos/<int:foto_id>/eliminar/', views.eliminar_foto, name='eliminar-foto'),

    # Endpoints del productor autenticado
    path('mis-productos/', views.mis_productos, name='mis-productos'),
]
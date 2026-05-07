from django.urls import path
from . import views

urlpatterns = [
    # Crear pedido desde una negociación
    path('crear/<int:negociacion_id>/', views.crear_pedido, name='crear-pedido'),

    # Lista de pedidos del usuario
    path('mis-pedidos/', views.mis_pedidos, name='mis-pedidos'),

    # Detalle de un pedido
    path('<int:pedido_id>/', views.detalle_pedido, name='detalle-pedido'),

    # Actualizar estado del pedido
    path('<int:pedido_id>/estado/', views.actualizar_estado, name='actualizar-estado'),

    # Calificar después de entrega
    path('<int:pedido_id>/calificar/', views.calificar, name='calificar'),
]
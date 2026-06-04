from django.urls import path
from . import views

urlpatterns = [
    # Recordatorios (cron gratuito externo; ver docs/CRON_GRATIS.md)
    path('cron/recordatorios/', views.ejecutar_recordatorios_cron, name='cron-recordatorios'),

    # Iniciar negociación sobre un producto
    path('iniciar/<int:producto_id>/', views.iniciar_negociacion, name='iniciar-negociacion'),

    # Lista de negociaciones del usuario
    path('mis-negociaciones/', views.mis_negociaciones, name='mis-negociaciones'),

    # Detalle de una negociación con todos sus mensajes
    path('<int:negociacion_id>/', views.detalle_negociacion, name='detalle-negociacion'),

    # Enviar mensaje en una negociación
    path('<int:negociacion_id>/mensajes/', views.enviar_mensaje, name='enviar-mensaje'),

    # Cambiar estado de la negociación
    path('<int:negociacion_id>/estado/', views.cambiar_estado_negociacion, name='cambiar-estado-negociacion'),
]
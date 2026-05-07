from django.urls import path
from . import views

urlpatterns = [
    path('', views.mis_notificaciones, name='mis-notificaciones'),
    path('no-leidas/', views.conteo_no_leidas, name='conteo-no-leidas'),
    path('<int:notificacion_id>/leer/', views.marcar_leida, name='marcar-leida'),
    path('leer-todas/', views.marcar_todas_leidas, name='marcar-todas-leidas'),
]
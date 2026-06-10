from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Autenticación
    path('registro/', views.registro, name='registro'),
    path('verificar-email/', views.verificar_email, name='verificar-email'),
    path('login/', views.login, name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # Perfil
    path('perfil/', views.perfil, name='perfil'),
    path('cambiar-password/', views.cambiar_password, name='cambiar-password'),

    # Recuperacion de contrasena
    path('recuperar-password/', views.solicitar_recuperacion, name='solicitar-recuperacion'),
    path('confirmar-recuperacion/', views.confirmar_recuperacion, name='confirmar-recuperacion'),

    # Datos de referencia
    path('municipios/', views.listar_municipios, name='listar-municipios'),
]
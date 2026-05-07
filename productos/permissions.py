from rest_framework.permissions import BasePermission


class EsProductor(BasePermission):
    """
    Permiso que solo permite acceso a usuarios con rol de productor.
    Se usa en los endpoints de creación y gestión de productos.
    """
    message = 'Solo los productores pueden realizar esta acción.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.es_productor
        )


class EsProductorOSoloLectura(BasePermission):
    """
    Permite lectura a cualquier usuario autenticado,
    pero escritura solo a productores.
    Se usa en el catálogo público.
    """
    message = 'Solo los productores pueden crear o modificar productos.'

    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return (
            request.user and
            request.user.is_authenticated and
            request.user.es_productor
        )
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permissão customizada que permite que apenas o dono do objeto possa editá-lo.
    """
    def has_object_permission(self, request, view, obj):
        # Permissões de leitura são permitidas para qualquer solicitação,
        # então vamos sempre permitir GET, HEAD ou OPTIONS.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Permissão de escrita apenas se o usuário for o dono do objeto.
        return obj.owner == request.user

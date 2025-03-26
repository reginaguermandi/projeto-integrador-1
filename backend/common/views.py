from django.shortcuts import render
from rest_framework import viewsets
from .models import User
from .serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_active=True)  # Só listar usuários ativos
    serializer_class = UserSerializer

    def perform_destroy(self, instance):
        """Sobrescreve a destruição padrão para aplicar exclusão lógica."""
        instance.delete()  # Vai chamar o método 'delete' que desativa o usuário
        
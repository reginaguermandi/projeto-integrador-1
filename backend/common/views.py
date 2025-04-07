from django.shortcuts import render
from rest_framework import viewsets, serializers, status
from .models import User, Book, BookRequest
from .serializers import UserSerializer, BookSerializer, BookRequestSerializer
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response

def update_book_status(book, status, clear_request=False):
    book.status = status
    if clear_request:
        book.book_request = None
    book.save()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_active=True)  # Só listar usuários ativos
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    # Definindo permissões por ação
    def get_permissions(self):
        if self.action == 'create':
            # Permite acesso sem autenticação para criar um novo usuário
            return [AllowAny()]
        # Para outras ações (como update, delete), exige autenticação
        return [IsAuthenticated()]
    
    def perform_destroy(self, instance):
        """Sobrescreve a destruição padrão para aplicar exclusão lógica."""
        instance.delete() 
    
    def get_queryset(self):
    # Se não for admin, o usuário só pode ver seus próprios dados
        if not self.request.user.is_staff:
            return User.objects.filter(id=self.request.user.id)
        return super().get_queryset()


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user

        if self.action == 'list' and 'my-books' in self.request.path:
            return Book.objects.filter(user=user)

        return Book.objects.filter(status='available')
    
    def get_permissions(self):
        if self.action == 'list' and 'catalog' in self.request.path:
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Atribuir o dono do livro ao usuário logado."""
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        book = self.get_object()
        if book.status != 'available':
            raise serializers.ValidationError("Apenas livros disponíveis podem ser editados.")
        serializer.save()

class BookRequestViewSet(viewsets.ModelViewSet):
    queryset = BookRequest.objects.all()
    serializer_class = BookRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filtra os pedidos apenas do usuário autenticado
        return BookRequest.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Atualizar o status do livro para 'requested'
        book_request = serializer.save()
        update_book_status(book_request.book, 'requested')

    def perform_update(self, serializer):
        instance = serializer.save()
        book = instance.book

        # Se o status do pedido for alterado para "approved" ou "denied", limpar o campo `book_request` do livro
        if instance.status == 'approved':
            update_book_status(book, 'unavailable', clear_request=True)
        elif instance.status == 'denied':
            # Se o pedido for negado, liberar o livro para ser requisitado novamente
            update_book_status(book, 'available', clear_request=True)

    def cancelar(self, request, pk=None):
        book_request = self.get_object()

        # Verifica se o usuário é o dono da solicitação
        if book_request.user != request.user:
            return Response({"detail": "Você não tem permissão para cancelar este pedido."}, status=status.HTTP_403_FORBIDDEN)

        # Atualiza status do pedido e do livro
        book_request.status = 'cancelled'
        book_request.save()

        update_book_status(book_request.book, 'available', clear_request=True)

        return Response({"detail": "Pedido cancelado com sucesso."}, status=status.HTTP_200_OK)

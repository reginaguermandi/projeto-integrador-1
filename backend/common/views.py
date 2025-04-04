from django.shortcuts import render
from rest_framework import viewsets
from .models import User, Book, BookRequest
from .serializers import UserSerializer, BookSerializer, BookRequestSerializer
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny

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

        if self.action == 'list' and 'mybooks' in self.request.path:
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

    def perform_create(self, serializer):
        book = serializer.validated_data['book']

        # Verificar se já existe uma solicitação pendente para o livro
        existing_request = BookRequest.objects.filter(book=book, status='pending').first()
        if existing_request:
            raise serializer.ValidationError("Este livro já tem um pedido pendente.")

        # Verificar se o livro está disponível
        if book.status != 'available':
            raise serializer.ValidationError("Este livro não está disponível para doação")

        # Atualizar o status do livro para 'requested' (ou outro status apropriado)
        book.status = 'requested'  # ou outro status que você queira indicar que foi solicitado
        book.save()

        # Atribuir a solicitação ao usuário logado
        book_request = serializer.save(user=self.request.user)

        # Atualizar o campo `book_request` no livro
        book.book_request = book_request
        book.save()

    def perform_update(self, serializer):
        instance = serializer.save()
        book = instance.book

    # Se o status do pedido for alterado para "approved" ou "denied", limpar o campo `book_request` do livro
        if instance.status == 'approved':
            book.status = 'unavailable'  # Ou outro status apropriado para livros doados
            book.book_request = None  # Limpa o campo book_request
            book.save()
        elif instance.status == 'denied':
             # Se o pedido for negado, liberar o livro para ser requisitado novamente
            book.status = 'available'
            book.book_request = None
            book.save()


from django.shortcuts import render
from rest_framework import viewsets, serializers, status
from .models import User, Book, BookRequest
from .serializers import UserSerializer, BookSerializer, BookRequestSerializer
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response

def update_book_status(book, status, clear_request=False):
    """Atualiza o status do livro e limpa o campo book_request, se necessário."""
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
        """Sobrescreve a destruição padrão para verificar solicitações em aberto."""
        # Verificar se o usuário possui solicitações pendentes como solicitante
        open_requests_as_requester = BookRequest.objects.filter(user=instance, status='pending')

        # Verificar se o usuário possui solicitações pendentes como doador
        open_requests_as_donor = BookRequest.objects.filter(book__user=instance, status='pending')

        if open_requests_as_requester.exists() or open_requests_as_donor.exists():
            # Verificar se o cliente confirmou a exclusão
            confirm = self.request.query_params.get('confirm', 'false').lower()
            if confirm != 'true':
                # Retornar mensagem informando sobre as solicitações em aberto
                response = {
                    "detail": "O usuário possui solicitações de livros em aberto. Deseja continuar e cancelar essas solicitações?",
                    "open_requests_as_requester": [
                        {"id": req.id, "book_title": req.book.title} for req in open_requests_as_requester
                    ],
                    "open_requests_as_donor": [
                        {"id": req.id, "book_title": req.book.title, "requester": req.user.name} for req in open_requests_as_donor
                    ]
                }
                raise serializers.ValidationError(response)

            # Caso o cliente confirme, tratar as solicitações pendentes
            # 1. Se for solicitante, cancelar as solicitações e liberar os livros
            for request in open_requests_as_requester:
                update_book_status(request.book, 'available', clear_request=True)
                request.status = 'cancelled'
                request.save()

            # 2. Se for doador, cancelar as solicitações e excluir os livros
            for request in open_requests_as_donor:
                request.status = 'cancelled'
                request.save()

            # Excluir todos os livros do usuário doador
            instance.books.all().delete()

        # Desativar o usuário
        instance.is_active = False
        instance.save()
    
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
        book = serializer.validated_data['book_id']
        user = self.request.user 

        if book.user == user:
            raise serializers.ValidationError("Você não pode solicitar um livro que você mesmo cadastrou.")

        # Verificar se já existe uma solicitação pendente para o livro
        existing_request = BookRequest.objects.filter(book=book, status='pending').first()
        if existing_request:
            raise serializers.ValidationError("Este livro já tem um pedido pendente.")

        # Verificar se o livro está disponível
        if book.status != 'available':
            raise serializers.ValidationError("Este livro não está disponível para doação")

        # Atualizar o status do livro para 'requested' (ou outro status apropriado)
        update_book_status(book, 'requested')

        # Atribuir a solicitação ao usuário logado
        book_request = serializer.save(user=self.request.user)

        # Atualizar o campo `book_request` no livro
        book.book_request = book_request
        book.save()

    def perform_update(self, serializer):
        instance = serializer.save()
        book = instance.book

        # Atualizar o status do livro com base no status da solicitação
        if instance.status == 'awaiting_pickup':
            # O livro está aguardando retirada
            update_book_status(book, 'unavailable', clear_request=False)
        elif instance.status == 'delivered':
            # O livro foi entregue, não está mais disponível
            update_book_status(book, 'unavailable', clear_request=True)
        elif instance.status == 'cancelled':
            # Se o pedido for cancelado, liberar o livro para ser requisitado novamente
            update_book_status(book, 'available', clear_request=True)

    @action(detail=True, methods=['patch'], url_path='confirm-pickup')
    def confirmar_retirada(self, request, pk=None):
        """Confirma a retirada do livro pelo solicitante."""
        book_request = self.get_object()

        # Verifica se o usuário é o solicitante
        if book_request.user != request.user:
            return Response({"detail": "Você não tem permissão para confirmar a retirada deste pedido."}, status=status.HTTP_403_FORBIDDEN)

        # Atualizar o status da solicitação para 'delivered'
        book_request.status = 'delivered'
        book_request.save()

        # Atualizar o status do livro para 'unavailable' e limpar o campo book_request
        update_book_status(book_request.book, 'unavailable', clear_request=True)

        return Response({"detail": "Retirada confirmada com sucesso. O livro foi marcado como entregue."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='cancel-request')
    def cancelar(self, request, pk=None):
        """Cancela a solicitação pelo solicitante."""
        book_request = self.get_object()

        # Verifica se o usuário é o solicitante
        if book_request.user != request.user:
            return Response({"detail": "Você não tem permissão para cancelar este pedido."}, status=status.HTTP_403_FORBIDDEN)

        # Atualizar o status da solicitação para 'cancelled'
        book_request.status = 'cancelled'
        book_request.save()

        # Atualizar o status do livro para 'available' e limpar o campo book_request
        update_book_status(book_request.book, 'available', clear_request=True)

        return Response({"detail": "Solicitação cancelada com sucesso. O livro voltou a ficar disponível no catálogo."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='cancelar')
    def cancelar(self, request, pk=None):
        book_request = self.get_object()

        # Verifica se o usuário é o dono da solicitação
        if book_request.user != request.user:
            return Response({"detail": "Você não tem permissão para cancelar este pedido."}, status=status.HTTP_403_FORBIDDEN)

        # Atualiza o status do pedido para 'cancelled'
        book_request.status = 'cancelled'
        book_request.save()

        # Atualiza o status do livro para 'available' e limpa o campo book_request
        update_book_status(book_request.book, 'available', clear_request=True)

        return Response({"detail": "Pedido cancelado com sucesso."}, status=status.HTTP_200_OK)

class DonorBookRequestViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Lista as solicitações associadas aos livros do usuário logado."""
        user = request.user
        book_requests = BookRequest.objects.filter(book__user=user)
        serializer = BookRequestSerializer(book_requests, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='approve')
    def approve_request(self, request, pk=None):
        """Aprova uma solicitação de livro."""
        try:
            book_request = BookRequest.objects.get(pk=pk, book__user=request.user)
        except BookRequest.DoesNotExist:
            return Response({"detail": "Solicitação não encontrada ou você não tem permissão para aprová-la."}, status=status.HTTP_404_NOT_FOUND)

        # Atualizar o status da solicitação para 'awaiting_pickup'
        book_request.status = 'awaiting_pickup'
        book_request.save()

        # Atualizar o status do livro para 'unavailable'
        book_request.book.status = 'unavailable'
        book_request.book.save()

        return Response({"detail": "Solicitação aprovada com sucesso. O livro está aguardando retirada."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='deny')
    def deny_request(self, request, pk=None):
        """Nega uma solicitação de livro."""
        try:
            book_request = BookRequest.objects.get(pk=pk, book__user=request.user)
        except BookRequest.DoesNotExist:
            return Response({"detail": "Solicitação não encontrada ou você não tem permissão para negá-la."}, status=status.HTTP_404_NOT_FOUND)

        # Atualizar o status da solicitação para 'cancelled'
        book_request.status = 'cancelled'
        book_request.save()

        # Atualizar o status do livro para 'available' e limpar o campo book_request
        book = book_request.book
        book.status = 'available'
        book.book_request = None  # Limpa o campo book_request
        book.save()

        return Response({"detail": "Solicitação negada com sucesso. O livro está disponível no catálogo."}, status=status.HTTP_200_OK)

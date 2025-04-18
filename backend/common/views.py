from django.shortcuts import render
from rest_framework import viewsets, serializers, status
from .models import User, Book, BookRequest, PickupPoint
from .serializers import UserSerializer, BookSerializer, BookRequestSerializer, PickupPointSerializer
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework.viewsets import ReadOnlyModelViewSet


def update_book_status(book, status, clear_request=False):
    """Atualiza o status do livro e limpa o campo book_request, se necessário."""
    book.status = status
    if clear_request:
        book.book_request = None
    book.save()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_active=True)
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
        # Verificar se o usuário possui solicitações pendentes como solicitante
        open_requests_as_requester = BookRequest.objects.filter(
            user=instance, status__in=['pending', 'awaiting_pickup']
        )

        # Verificar se o usuário possui solicitações pendentes como doador
        open_requests_as_donor = BookRequest.objects.filter(
            book__user=instance, status__in=['pending', 'awaiting_pickup']
        )

        # Se houver solicitações pendentes, solicitar confirmação antes de excluir
        if open_requests_as_requester.exists() or open_requests_as_donor.exists():
            confirm = self.request.query_params.get('confirm', 'false').lower()
            if confirm != 'true':
                # Retornar mensagem com detalhes das solicitações pendentes
                response = {
                    "detail": "Você possui solicitações de livros em aberto. Deseja continuar e cancelar essas solicitações?",
                    "open_requests_as_requester": [
                        {"id": req.id, "book_title": req.book.title} for req in open_requests_as_requester
                    ],
                    "open_requests_as_donor": [
                        {"id": req.id, "book_title": req.book.title, "requester": req.user.name} for req in open_requests_as_donor
                    ]
                }
                raise serializers.ValidationError(response)

            # Caso o cliente confirme a exclusão, cancelar as solicitações pendentes
            for request in open_requests_as_requester:
                update_book_status(request.book, 'available', clear_request=True)
                request.status = 'cancelled'
                request.save()

            for request in open_requests_as_donor:
                request.status = 'cancelled'
                request.save()

        # Excluir todos os livros disponíveis do usuário
        instance.books.filter(status='available').delete()

        # Desativar o usuário (soft delete)
        instance.is_active = False
        instance.save()
    
    def get_queryset(self):
        if not self.request.user.is_staff:
            return User.objects.filter(id=self.request.user.id)
        return super().get_queryset()

class PickupPointViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PickupPoint.objects.all()
    serializer_class = PickupPointSerializer

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self): 
        user = self.request.user
        return Book.objects.filter(user=user)

    def perform_create(self, serializer):
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

        update_book_status(book, 'requested')
        book_request = serializer.save(user=self.request.user)

        book.book_request = book_request
        book.save()

    def perform_update(self, serializer):
        instance = serializer.save()
        book = instance.book

        # Atualizar o status do livro com base no status da solicitação
        if instance.status == 'awaiting_pickup':
            update_book_status(book, 'unavailable', clear_request=False)
        elif instance.status == 'delivered':
            update_book_status(book, 'unavailable', clear_request=True)
        elif instance.status == 'cancelled':
            update_book_status(book, 'available', clear_request=True)

    @action(detail=True, methods=['patch'], url_path='confirm-pickup')
    def confirm_pickup(self, request, pk=None):
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
    def cancel_request(self, request, pk=None):
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

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
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

class CatalogViewSet(ReadOnlyModelViewSet):
    """
    ViewSet para listar livros disponíveis publicamente e exibir detalhes de um livro.
    """
    queryset = Book.objects.filter(status='available')
    permission_classes = [AllowAny]
    serializer_class = BookSerializer
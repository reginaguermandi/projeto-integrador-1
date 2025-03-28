from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, BookViewSet, BookRequestViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Criando um roteador para as views do Django Rest Framework
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'books', BookViewSet)
router.register(r'book_requests', BookRequestViewSet)

urlpatterns = [
    path('api/', include(router.urls)),

    # Rota para obter o token (login)
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # Rota para renovar o token
    path('api/login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
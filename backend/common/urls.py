from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

# Criando um roteador para as views do Django Rest Framework
router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
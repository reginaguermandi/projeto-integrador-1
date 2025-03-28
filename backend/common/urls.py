from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, BookViewSet, BookRequestViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'books', BookViewSet)
router.register(r'book_requests', BookRequestViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/books/meuslivros', BookViewSet.as_view({'get': 'list'}), name='meus-livros'),
    path('api/books/catalogo', BookViewSet.as_view({'get': 'list'}), name='catalogo-livros'),
]
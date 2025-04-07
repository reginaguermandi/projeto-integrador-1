from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, BookViewSet, BookRequestViewSet, DonorBookRequestViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'book_requests', BookRequestViewSet)
router.register(r'donor-requests', DonorBookRequestViewSet, basename='donor-requests')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/my-books/', BookViewSet.as_view({'get': 'list', 'post': 'create'}), name='my-books'),
    path('api/my-books/<int:pk>/', BookViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='my-book-details'),
    path('api/books/catalog', BookViewSet.as_view({'get': 'list'}), name='book-catalog'),
    path('api/book_requests/<int:pk>/cancelar/', BookRequestViewSet.as_view({'post': 'cancelar'}), name='bookrequest-cancelar'),
]
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework import routers

from users.views import UserViewSet, UserLoginView, PasswordResetViewSet
from main.views import PricelistUploadViewSet, ProductViewSet, OrderViewSet, CartViewSet

router = routers.SimpleRouter()
router.register(r'upload', PricelistUploadViewSet, 'upload-pricelist')
router.register(r'products', ProductViewSet, 'products')
router.register(r'orders', OrderViewSet, 'orders')
router.register(r'cart', CartViewSet, 'cart')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include([
        path('profile/', UserViewSet.as_view(
            {'get': 'retrieve', 'patch': 'partial_update'}),
             kwargs={'pk': 'me', 'name': 'profile'},
             name='user-profile'
             ),
        path('login/', UserLoginView.as_view(), name='user-login'),
        path('register/', UserViewSet.as_view({'post': 'create'}), name='user-register'),
        path('reset/', PasswordResetViewSet.as_view(), name='user-reset-password'),
    ])),
    path('', include(router.urls)),
]

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema')),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema')),
]

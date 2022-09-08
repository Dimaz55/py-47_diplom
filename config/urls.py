from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import routers

from users.views import UserViewSet, UserLoginView, PasswordResetViewSet
from main.views import PricelistUploadViewSet, ProductViewSet

router = routers.SimpleRouter()
router.register(r'upload', PricelistUploadViewSet, 'upload')
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include([
        path('profile/', UserViewSet.as_view(
            {'get': 'retrieve', 'patch': 'partial_update'}), kwargs={'pk': 'me'}),
        path('login/', UserLoginView.as_view()),
        path('register/', UserViewSet.as_view({'post': 'create'})),
        path('reset/', PasswordResetViewSet.as_view()),
    ])),
    path('', include(router.urls)),
]


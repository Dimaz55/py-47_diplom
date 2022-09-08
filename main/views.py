from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

from main.models import PricelistFile, Variant
from main.serializers import (
    PricelistUploadSerializer,
    ProductDetailSerializer,
    ProductListSerializer
)
from users.permissions import IsSeller


class PricelistUploadViewSet(viewsets.GenericViewSet,
                             mixins.CreateModelMixin,
                             mixins.RetrieveModelMixin):
    queryset = PricelistFile.objects.all()
    serializer_class = PricelistUploadSerializer
    permission_classes = [IsAuthenticated, IsSeller]
    basename = 'upload'

    def get_queryset(self):
        queryset = self.get_queryset()
        return queryset.filter(seller=self.request.user)

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Variant.objects.prefetch_related('product', 'pricelist')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer

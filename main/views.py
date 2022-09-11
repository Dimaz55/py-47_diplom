from django.db.models.functions import Now
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from main.models import PricelistFile, Variant, Order, OrderItem
from main.serializers import (
    PricelistUploadSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    SellerOrderDetailSerializer,
    SellerOrderListSerializer,
    CartSerializer,
    OrderItemSerializer,
    BuyerOrderDetailSerializer,
    BuyerOrderListSerializer,
)
from main.tasks import send_order_emails
from users.permissions import IsSeller, IsBuyer, OrderPermission


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


class OrderViewSet(viewsets.GenericViewSet,
                   mixins.RetrieveModelMixin,
                   mixins.ListModelMixin,
                   mixins.UpdateModelMixin):
    permission_classes = [OrderPermission]
    queryset = Order.objects.all()

    def get_serializer_class(self):
        if self.request.user.role == 'seller':
            if self.action == 'retrieve':
                return SellerOrderDetailSerializer
            return SellerOrderListSerializer
        if self.action == 'retrieve':
            return BuyerOrderDetailSerializer
        return BuyerOrderListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == 'buyer':
            return queryset.filter(customer=user).exclude(status='in_cart')
        else:
            return queryset.exclude(status='in_cart').filter(items__seller=user).distinct()


class CartViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated, IsBuyer]
    serializer_class = CartSerializer

    # фильтр: только своя неотправленная в заказ корзина
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(customer=self.request.user, status='in_cart')

    # При запросе списка получаем корзину покупателя или создаём пустую
    def list(self, request, *args, **kwargs):
        obj, created = Order.objects.get_or_create(
            customer=request.user, status='in_cart')
        return Response(self.serializer_class(obj).data)

    def create(self, request, *args, **kwargs):
        # Получаем корзину если есть либо создаём пустую
        cart, _ = Order.objects.get_or_create(
            customer=request.user, status='in_cart')
        # Если корзина пуста - наполняем товарами из запроса
        if not cart.items.all():
            items = request.data.pop('items')
            serializer = OrderItemSerializer(data=items, many=True)
            serializer.is_valid(raise_exception=True)
            for item in serializer.validated_data:
                OrderItem.objects.create(
                    order=cart,
                    pricelist=item['pricelist'],
                    quantity=item['quantity'])
        # Если в корзине товары - удаляем и наполняем товарами из запроса
        else:
            items = request.data.pop('items')
            cart.order_items.all().delete()
            serializer = OrderItemSerializer(data=items, many=True)
            serializer.is_valid(raise_exception=True)
            new_items = serializer.create(serializer.validated_data)
            cart.order_items.set(new_items)
        cart.refresh_from_db()
        return Response(self.serializer_class(cart).data)

    # При создании корзины прописываем её владельца
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)

    # очистка корзины
    @action(methods=['DELETE'], detail=False, url_path='clear')
    def cart_clear(self, request):
        cart = request.user.orders.filter(status='in_cart').first()
        if cart:
            cart.order_items.all().delete()
        return Response(CartSerializer(cart).data)

    @action(methods=['POST'], detail=False, url_path='checkout')
    def cart_checkout(self, request):
        cart = request.user.orders.filter(status='in_cart').first()
        if cart:
            items = cart.order_items.all()
            for item in items:
                if item.quantity > item.pricelist.in_stock:
                    raise ValidationError({
                        'pricelist_id': item.pricelist.id,
                        'product': item.pricelist.variant,
                        'in_stock': item.pricelist.in_stock
                    })
            if 'address' not in request.data:
                return Response({'error': 'field `address` required for order processing'})
            if request.data['address'] == '':
                return Response({'error': 'field `address` cannot be blank'})
            cart.address = request.data['address']
            cart.status = 'accepted'
            cart.created_at = Now()
            cart.save()
            send_order_emails.delay(cart.id)
        return Response(BuyerOrderDetailSerializer(cart).data)

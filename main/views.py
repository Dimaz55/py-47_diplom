from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from main import examples
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
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(seller=self.request.user)
    
    @extend_schema(summary='Выгрузка прайс-листа')
    def create(self, request, *args, **kwargs):
        """
        Формат файла CSV. Структура полей:
        
        Категория,Бренд,Модель,Артикул,Количество,Цена товара,Цена доставки,
        (Название характеристики,Значение характеристики)...
        """
        return super().create(request, *args, **kwargs)
        
    def perform_create(self, serializer):
        """Привязка выгруженного файла к продавцу"""
        serializer.save(seller=self.request.user)

    @extend_schema(summary='Просмотр результата выгрузки прайс-листа')
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Variant.objects.prefetch_related('product', 'pricelist')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer

    @extend_schema(summary='Просмотр списка товаров')
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary='Просмотр информации о товаре')
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    

class OrderViewSet(viewsets.GenericViewSet,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin):
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
    
    @extend_schema(
        operation_id='orders-list',
        responses=BuyerOrderListSerializer,
        examples=[
            OpenApiExample(
                name='Заказы покупателя',
                value=examples.BUYER_ORDER_LIST,
                response_only=True,
                status_codes=[200]
            ),
            OpenApiExample(
                name='Заказы продавца',
                value=examples.SELLER_ORDER_LIST,
                response_only=True,
                status_codes=[200]
            )
        ],
        summary='Получение списка заказов'
    )
    def list(self, request, *args, **kwargs):
        """
        Выдача зависит от роли пользователя
        """
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary='Детальная информация о заказе',
        parameters=None,
        request=None,
        responses=[BuyerOrderDetailSerializer, SellerOrderDetailSerializer],
        examples=[
            OpenApiExample(
                name='Заказ покупателя',
                value=examples.BUYER_ORDER_DETAIL,
                status_codes=[200],
                response_only=True
            ),
            OpenApiExample(
                name='Заказ продавца',
                value=examples.SELLER_ORDER_DETAIL,
                status_codes=[200],
                response_only=True
            )
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Для продавца доступны только заказы с его товарами.
        Для покупателя доступны только его заказы.
        """
        return super().retrieve(request, *args, **kwargs)


class CartViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated, IsBuyer]
    serializer_class = CartSerializer
    http_method_names = ['get', 'post', 'delete']
    
    # фильтр: только своя неотправленная в заказ корзина
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(customer=self.request.user, status='in_cart')
    
    # При запросе списка получаем корзину покупателя или создаём пустую
    @extend_schema(
        summary='Просмотр корзины',
        examples=[
            OpenApiExample(
                name='Содержимое корзины',
                value=examples.CART_CONTENTS,
                status_codes=[200],
                response_only=True
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        obj, created = Order.objects.get_or_create(
            customer=request.user, status='in_cart')
        return Response(self.serializer_class(obj).data)
    
    @extend_schema(
        summary='Добавление товаров в корзину',
        examples=[
            OpenApiExample(
                name='Добавление товаров',
                value={'items': [{'pricelist': 0, 'quantity': 0}], 'address': 'string'},
                status_codes=[200],
                request_only=True
            ),
            OpenApiExample(
                name='Содержимое корзины',
                value=examples.CART_CONTENTS,
                status_codes=[201],
                response_only=True
            )
        ]
    )
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
        return Response(self.serializer_class(cart).data, status=201)
    
    # При создании корзины прописываем её владельца
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)
    
    @extend_schema(summary='Очистка корзины')
    @action(methods=['DELETE'], detail=False, url_path='clear')
    def cart_clear(self, request):
        cart = request.user.orders.filter(status='in_cart').first()
        if cart:
            cart.order_items.all().delete()
        return Response(status=204)
    
    @extend_schema(
        summary='Отправка корзины в заказ',
        parameters=None,
        examples=[
            OpenApiExample(
                name='Адрес доставки',
                value={'address': 'string'},
                request_only=True,
                status_codes=[200]
            ),
            OpenApiExample(
                name='Созданный заказ',
                value=examples.CART_CONTENTS,
                response_only=True,
                status_codes=[200]
            )
        ]
    )
    @action(methods=['POST'], detail=False, url_path='checkout')
    def cart_checkout(self, request):
        """
        Для отправки заказа обязательно указать адрес доставки (поле address).
        """
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
            cart.created_at = timezone.now()
            cart.save()
            send_order_emails.delay(cart.id)
        else:
            raise ValidationError({'error': 'cart is empty'})
        return Response(BuyerOrderDetailSerializer(cart).data)
    
    # Исключение методов из swagger
    @extend_schema(exclude=True)
    def retrieve(self, request, *args, **kwargs):
        pass
    
    @extend_schema(exclude=True)
    def destroy(self, request, *args, **kwargs):
        pass

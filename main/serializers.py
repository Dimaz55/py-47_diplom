from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse

from main.models import PricelistFile, Variant, Property, Pricelist, Order, OrderItem
from main.tasks import parse_pricelist
from main.utils import get_totals


class PricelistUploadSerializer(serializers.ModelSerializer):
    result_check_endpoint = serializers.SerializerMethodField()
    file = serializers.FileField(write_only=True)
    upload_result = serializers.JSONField(default={'status': 'parsing'})
    
    class Meta:
        model = PricelistFile
        fields = ['file', 'upload_result', 'result_check_endpoint']
    
    def create(self, validated_data):
        instance = super().create(validated_data)
        parse_pricelist.delay(instance.id)
        return instance
    
    @extend_schema_field(serializers.URLField)
    def get_result_check_endpoint(self, obj) -> str:
        request = self.context['request']
        return reverse('upload-detail', kwargs={'pk': obj.id}, request=request)


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ['title', 'value']


class PricelistSerializer(serializers.ModelSerializer):
    seller = serializers.CharField(source='seller.company')
    
    class Meta:
        model = Pricelist
        fields = [
            'id', 'product_price', 'delivery_price', 'seller', 'in_stock',
            'price_date'
        ]


class ProductListSerializer(serializers.ModelSerializer):
    brand = serializers.CharField(source='product.brand.title')
    title = serializers.CharField(source='product.title')
    category = serializers.CharField(source='product.category.title')
    prices = PricelistSerializer(many=True)
    
    class Meta:
        model = Variant
        fields = ['id', 'sku', 'brand', 'title', 'category', 'prices']


class ProductDetailSerializer(serializers.ModelSerializer):
    brand = serializers.CharField(source='product.brand.title')
    title = serializers.CharField(source='product.title')
    category = serializers.CharField(source='product.category.title')
    props = PropertySerializer(many=True)
    prices = PricelistSerializer(many=True)
    
    class Meta:
        model = Variant
        fields = ['id', 'sku', 'brand', 'title', 'category', 'props', 'prices']


class OrderPricelistSerializer(serializers.ModelSerializer):
    seller = serializers.CharField(source='seller.company')
    title = serializers.CharField(source='variant')
    
    class Meta:
        model = Pricelist
        fields = [
            'title', 'product_price', 'delivery_price', 'seller', 'in_stock',
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField(source='pricelist.variant')
    product_price = serializers.IntegerField(
        source='pricelist.product_price', required=False)
    delivery_price = serializers.IntegerField(
        source='pricelist.delivery_price', required=False)
    seller = serializers.StringRelatedField(source='pricelist.seller.company')
    
    class Meta:
        model = OrderItem
        fields = ['pricelist', 'product', 'product_price', 'delivery_price',
                  'quantity', 'seller']
        read_only_fields = ['product', 'product_price', 'delivery_price']
    
    def validate_quantity(self, value):
        pricelist = self.initial_data[0]['pricelist']
        obj = Pricelist.objects.filter(pk=pricelist).first()
        if obj:
            if value > obj.in_stock:
                raise ValidationError({
                    'pricelist_id': obj.id,
                    'product': obj.variant,
                    'in stock': obj.in_stock
                })
            return value


class OrderSerializer(serializers.ModelSerializer):
    summary = serializers.SerializerMethodField()
    items = OrderItemSerializer(source='order_items', many=True)
    
    @extend_schema_field(serializers.JSONField)
    def get_summary(self, obj):
        items = obj.order_items.all()
        if 'request' in self.context:
            user = self.context['request'].user
            if user and user.role == 'seller':
                items = obj.order_items.filter(pricelist__seller=user)
        products, delivery = get_totals(items)
        return {'products_total': products,
                'delivery_total': delivery,
                'total': products + delivery}


class SellerOrderItemSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField(source='pricelist.variant')
    sku = serializers.CharField(source='pricelist.variant.sku')
    product_price = serializers.IntegerField(
        source='pricelist.product_price', required=False)
    delivery_price = serializers.IntegerField(
        source='pricelist.delivery_price', required=False)
    in_stock = serializers.IntegerField(
        source='pricelist.in_stock', required=False)
    
    class Meta:
        model = OrderItem
        fields = ['pricelist', 'product', 'sku', 'product_price', 'delivery_price',
                  'quantity', 'in_stock']
        read_only_fields = ['product', 'product_price', 'sku',
                            'delivery_price', 'seller_stock', 'customer']


class SellerOrderSerializer(OrderSerializer):
    customer = serializers.StringRelatedField()
    customer_company = serializers.CharField(source='customer.company')


class SellerOrderListSerializer(SellerOrderSerializer):
    delivery_address = serializers.CharField(source='address')
    
    class Meta:
        model = Order
        fields = ['id', 'customer', 'customer_company', 'delivery_address', 'status', 'summary']


class SellerOrderDetailSerializer(SellerOrderSerializer):
    items = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'customer', 'customer_company', 'status', 'address', 'created_at',
                  'summary', 'items']
    
    def get_items(self, obj):
        user = self.context['request'].user
        items = obj.order_items.filter(pricelist__seller=user)
        return SellerOrderItemSerializer(items, many=True).data


class CartSerializer(OrderSerializer):
    class Meta:
        model = Order
        fields = ['id', 'summary', 'items', 'address']
        read_only_fields = ['status', 'customer']
    
    def create(self, validated_data):
        items = validated_data.pop('order_items')
        cart = Order.objects.create(**validated_data)
        for item in items:
            OrderItem.objects.create(
                order=cart, pricelist=item['pricelist'], quantity=item['quantity'])
        cart.refresh_from_db()
        return cart


class BuyerOrderListSerializer(OrderSerializer):
    class Meta:
        model = Order
        fields = ['id', 'status', 'address', 'summary']


class BuyerOrderDetailSerializer(OrderSerializer):
    class Meta:
        model = Order
        fields = ['id', 'status', 'created_at', 'address', 'items', 'summary']

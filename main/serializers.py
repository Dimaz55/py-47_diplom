from rest_framework import serializers
from rest_framework.reverse import reverse

from main.models import PricelistFile, Variant, Property, Pricelist
from main.tasks import parse_pricelist


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

    def get_result_check_endpoint(self, obj):
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
            'id', 'product_price', 'delivery_price', 'quantity', 'orderable', 'seller',
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
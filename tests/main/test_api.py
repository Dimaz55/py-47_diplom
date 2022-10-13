import os
import time

import pytest
from django.urls import reverse

from main.models import PricelistFile


@pytest.mark.django_db
class TestMain:
    # проверка прав пользователей на выгрузку прайс-листов
    # продавец может выгружать, статус 201, создаётся объект PricelistFile
    # покупатель не может выгружать, статус 403, PricelistFile не создаётся
    @pytest.mark.parametrize(
        'user_role, status_code, count',
        [
            ('seller', 201, 1),
            ('buyer', 403, 0)
        ]
    )
    def test_user_upload_pricelist_permission(
            self, api_client, user_factory, user_role, status_code, count,
            csv_pricelist):
        pricelist_count_before = PricelistFile.objects.count()
        user = user_factory(role=user_role)
        url = reverse('upload-list')
        api_client.force_authenticate(user)
        response = api_client.post(
            url, data={'file': csv_pricelist}, format='multipart')
        assert response.status_code == status_code
        assert PricelistFile.objects.count() == pricelist_count_before + count
    
    def test_product_list(self, api_client, product_factory):
        product_qty = 5
        products = product_factory(_quantity=product_qty)
        url = reverse('products-list')
        response = api_client.get(url)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == len(products)
    
    def test_product_retrieve(self, api_client, product_factory):
        product = product_factory()
        url = reverse('products-detail', kwargs={'pk': product.pk})
        response = api_client.get(url)
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
    
    @pytest.mark.parametrize(
        'user_role, status_code',
        [
            ('buyer', 201),
            ('seller', 403)
        ]
    )
    def test_put_items_in_cart(self, api_client, user_factory, product_factory,
                               products_data, user_role, status_code):
        products = product_factory(_quantity=2)
        user = user_factory(role=user_role)
        url = reverse('cart-list')
        api_client.force_authenticate(user)
        response = api_client.post(url, products_data(products))
        assert response.status_code == status_code
    
    

    
        
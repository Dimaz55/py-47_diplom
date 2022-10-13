import os

import pytest
from model_bakery import baker
from rest_framework.test import APIClient

from main.models import Variant, Pricelist


@pytest.fixture
def api_client():
    """Фикстура для клиента API."""
    return APIClient()


@pytest.fixture
def user_factory():
    """Фикстура для создания пользователей"""
    
    def factory(**kwargs):
        return baker.make('users.User', **kwargs)
    
    return factory


@pytest.fixture
def seller_data():
    return {
        'last_name': 'Testov',
        'first_name': 'Test',
        'patronymic': 'Testovich',
        'company': 'Test company',
        'email': 'test@example.com',
        'password': 'SuperPassword',
        'role': 'seller'
    }


@pytest.fixture
def buyer_data():
    return {
        'last_name': 'Testov',
        'first_name': 'Test',
        'patronymic': 'Testovich',
        'company': 'Test company',
        'email': 'test@example.com',
        'password': 'SuperPassword',
        'role': 'buyer'
    }


@pytest.fixture
def csv_pricelist():
    content = f'Категория,Бренд,Модель,Количество,Цена,Цена доставки,Название характеристики,' \
              f'Значение,Название характеристики,Значение,Название характеристики,Значение\n' \
              f'Test category,Test brand,Test model,test_sku,1,1,1,Test attr title 1,' \
              f'Test attr value 1\n'
    with open('test_price.csv', 'x+') as file:
        file.writelines(content)
        file.seek(0)
        yield file
    os.remove('test_price.csv')


@pytest.fixture
def product_factory():
    def factory(**kwargs):
        seller = baker.make('users.User', role='seller')
        properties = baker.prepare('main.Property', _quantity=2)
        variants = baker.make(
            'main.Variant', props=properties, **kwargs)
        if isinstance(variants, list):
            for variant in variants:
                Pricelist.objects.create(
                    variant=variant, seller=seller, in_stock=5)
        return variants
    
    return factory


@pytest.fixture
def order_factory():
    def factory(**kwargs):
        items = baker.make('main.Pricelist', _quantity=5)
        return baker.make('main.Order', items=items, **kwargs)
    
    return factory


@pytest.fixture
def products_data():
    def product_dict(*args):
        return {
            'items': [{'pricelist': product.prices.first().id, 'quantity': 1}
                      for product in args[0]]
        }
    return product_dict

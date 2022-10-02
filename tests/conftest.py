import pytest
from model_bakery import baker
from rest_framework.test import APIClient


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
		'first_name': 'Seller',
		'company': 'Sales Inc.',
		'email': 'testov@seller-email.com',
		'password': 'SuperPassword',
		'role': 'seller'
	}


@pytest.fixture
def buyer_data():
	return {
		'last_name': 'Testov',
		'first_name': 'Buyer',
		'company': 'Allbuy Co',
		'email': 'testov@buyer-email.com',
		'password': 'SuperPassword',
		'role': 'buyer'
	}
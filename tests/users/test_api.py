import pytest
from django.urls import reverse

from users.models import User


@pytest.mark.django_db
def test_create_seller(api_client, seller_data):
    user_count = User.objects.count()
    url = reverse('user-register')
    response = api_client.post(url, data=seller_data)
    assert response.status_code == 201
    response_json = response.json()
    assert response_json['role'] == 'seller'
    assert User.objects.count() == user_count + 1
    

@pytest.mark.django_db
def test_user_login(api_client, user_factory):
    user = user_factory()
    password = User.objects.make_random_password()
    # Принудительно устанавливаем пароль чтобы можно было получить токен по API
    user.set_password(password)
    user.save()
    
    url = reverse('user-login')
    response = api_client.post(url, data={'email': user.email, 'password': password})
    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json['token'], str)

import pytest
from django.urls import reverse

from users.models import User


@pytest.mark.django_db
class TestUsers:
    def test_create_seller(self, api_client, seller_data):
        user_count = User.objects.count()
        url = reverse('user-register')
        response = api_client.post(url, data=seller_data)
        assert response.status_code == 201
        response_json = response.json()
        assert response_json['role'] == 'seller'
        assert User.objects.count() == user_count + 1

    def test_create_user_already_exists(self, api_client, user_factory,
                                        seller_data):
        user = user_factory()
        url = reverse('user-register')
        user_data = {
            'email': user.email,
            'password': 'random_password',
            'role': 'seller'
        }
        response = api_client.post(url, data=user_data)
        assert response.status_code == 400

    def test_user_login(self, api_client, user_factory):
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

    def test_user_login_wrong_password(self, db, api_client, user_factory):
        user = user_factory()
        password = User.objects.make_random_password()
        user.set_password(password)
        user.save()
        url = reverse('user-login')
        response = api_client.post(
            url, data={'email': user.email, 'password': password + 'a'})
        assert response.status_code == 401
        
    def test_user_profile_change(self, api_client, user_factory, seller_data):
        user = user_factory()
        api_client.force_authenticate(user)
        url = reverse('user-profile')
        response = api_client.patch(url, seller_data)
        assert response.status_code == 200
        user.refresh_from_db()
        assert response.json()['first_name'] == seller_data['first_name'] == \
               user.first_name
        assert response.json()['last_name'] == seller_data['last_name'] == \
               user.last_name
        assert response.json()['patronymic'] == seller_data['patronymic'] == \
               user.patronymic
        assert response.json()['company'] == seller_data['company'] == \
               user.company
    

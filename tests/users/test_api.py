import pytest
from django.urls import reverse

from users.models import User


@pytest.mark.django_db
class TestUsers:
    def test_create_user_success(self, api_client, user_factory):
        user_count = User.objects.count()
        user = user_factory()
        url = reverse('user-register')
        response = api_client.post(url, data=user)
        assert response.status_code == 201
        response_json = response.json()
        assert response_json['role'] == 'seller'
        assert User.objects.count() == user_count + 1
    
    def test_user_create_fail_with_blank_password(self, api_client, seller_data):
        user_count = User.objects.count()
        url = reverse('user-register')
        seller_data['password'] = ''
        response = api_client.post(url, data=seller_data)
        assert response.status_code == 400
        assert user_count == User.objects.count()
        
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

    def test_user_login_wrong_password(self, api_client, user_factory):
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
    
    def test_user_profile_does_not_change_read_only_fields(
            self, api_client, seller_data):
        user = User.objects.create(**seller_data)
        api_client.force_authenticate(user)
        url = reverse('user-profile')
        read_only_fields = {
            'role': 'buyer',
            'password': 'patched_password',
            'email': 'new_test_email@example.com'
        }
        response = api_client.patch(url, read_only_fields)
        assert response.status_code == 200
        user.refresh_from_db()
        assert response.json()['role'] == seller_data['role']
        assert response.json()['email'] == seller_data['email']
        assert 'password' not in response.json()
        assert not user.check_password(read_only_fields['password'])
    
    def test_user_reset_password(self, api_client, user_factory):
        user = user_factory()
        initial_password = user.password
        url = reverse('user-reset-password')
        response = api_client.post(url, data={'email': user.email})
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.password != initial_password
        
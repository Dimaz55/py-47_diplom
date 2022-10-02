from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class User(AbstractBaseUser):
    ROLES = (
        ('seller', 'Продавец'),
        ('buyer', 'Покупатель')
    )
    last_name = models.CharField('Фамилия', max_length=20)
    first_name = models.CharField('Имя', max_length=20)
    patronymic = models.CharField('Отчество', max_length=20, blank=True)
    email = models.EmailField('Адрес', max_length=255, unique=True)
    company = models.CharField('Компания', max_length=255)
    role = models.CharField('Должность', choices=ROLES, max_length=6)

    USERNAME_FIELD = 'email'

    objects = BaseUserManager()

    def __str__(self):
        return f'{self.last_name} {str(self.first_name)[0]}. ' \
               f'{str(self.patronymic)[0]+"." if self.patronymic else None}'

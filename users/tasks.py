from django.core.mail import EmailMessage

from config.django_celery import app


@app.task()
def send_registration_email(email, password):
    mail = {
        'subject': 'Регистрация',
        'body': f'Здравствуйте! Вы успешно зарегистрировались.'
                f'Ваш пароль {password}.',
        'to': [email]
    }
    EmailMessage(**mail).send()


@app.task()
def send_password_reset_email(email, password):
    mail = {
        'subject': 'Восстановление пароля',
        'body': f'Ваш новый пароль {password}',
        'to': [email]
    }
    EmailMessage(**mail).send()

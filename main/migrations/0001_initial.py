# Generated by Django 4.1 on 2022-09-08 06:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, unique=True, verbose_name='Название бренда')),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, unique=True, verbose_name='Название категории')),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('accepted', 'Принят'), ('confirmed', 'Подтверждён'), ('sent', 'Отправлен'), ('complete', 'Выполнен'), ('cancelled', 'Отменён')], max_length=9, verbose_name='Статус заказа')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to=settings.AUTH_USER_MODEL, verbose_name='Клиент')),
            ],
        ),
        migrations.CreateModel(
            name='Pricelist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_price', models.PositiveIntegerField(null=True, verbose_name='Цена товара')),
                ('delivery_price', models.PositiveIntegerField(null=True, verbose_name='Цена доставки')),
                ('quantity', models.SmallIntegerField(default=0, verbose_name='Количество')),
                ('orderable', models.BooleanField(default=False, verbose_name='Доступно для заказа')),
                ('price_date', models.DateTimeField(auto_now_add=True)),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prices', to=settings.AUTH_USER_MODEL, verbose_name='Продавец')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Название товара/модель')),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products_of_brand', to='main.brand', verbose_name='Бренд')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products_in_category', to='main.category', verbose_name='Категория товара')),
            ],
        ),
        migrations.CreateModel(
            name='Property',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Характеристика')),
                ('value', models.CharField(max_length=255, verbose_name='Значение')),
            ],
        ),
        migrations.CreateModel(
            name='Variant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sku', models.CharField(max_length=50, unique=True)),
                ('pricelist', models.ManyToManyField(through='main.Pricelist', to=settings.AUTH_USER_MODEL, verbose_name='Цены товара')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='main.product', verbose_name='Модификация товара')),
                ('props', models.ManyToManyField(to='main.property', verbose_name='Характеристики товара')),
            ],
        ),
        migrations.CreateModel(
            name='PricelistFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='', verbose_name='Прайс')),
                ('upload_result', models.JSONField(blank=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Продавец')),
            ],
        ),
        migrations.AddField(
            model_name='pricelist',
            name='variant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prices', to='main.variant', verbose_name='Модификация'),
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=0, verbose_name='Количество')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_items', to='main.order', verbose_name='Заказ')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_items', to='main.product', verbose_name='Товар')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Продавец')),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='items',
            field=models.ManyToManyField(through='main.OrderItem', to='main.product', verbose_name='Позиции заказа'),
        ),
        migrations.AlterUniqueTogether(
            name='pricelist',
            unique_together={('seller', 'variant')},
        ),
    ]
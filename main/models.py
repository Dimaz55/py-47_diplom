from django.db import models

from users.models import User


class Category(models.Model):
    title = models.CharField('Название категории', max_length=255, unique=True)


class Brand(models.Model):
    title = models.CharField('Название бренда', max_length=255, unique=True)


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name='Категория товара',
        related_name='products_in_category')
    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        verbose_name='Бренд',
        related_name='products_of_brand')
    title = models.CharField('Название товара/модель', max_length=255)


class Property(models.Model):
    title = models.CharField('Характеристика', max_length=255)
    value = models.CharField('Значение', max_length=255)


class Pricelist(models.Model):
    seller = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Продавец', related_name='prices')
    variant = models.ForeignKey(
        'Variant', on_delete=models.CASCADE, verbose_name='Модификация', related_name='prices')
    product_price = models.PositiveIntegerField('Цена товара', null=True)
    delivery_price = models.PositiveIntegerField('Цена доставки', null=True)
    quantity = models.SmallIntegerField('Количество', default=0)
    orderable = models.BooleanField('Доступно для заказа', default=False)
    price_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['seller', 'variant']


class PricelistFile(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Продавец')
    file = models.FileField(verbose_name='Прайс')
    upload_result = models.JSONField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Variant(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Модификация товара',
        related_name='variants')
    props = models.ManyToManyField(Property, verbose_name='Характеристики товара')
    pricelist = models.ManyToManyField(
        User, through=Pricelist, verbose_name='Цены товара')


class OrderItem(models.Model):
    order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        verbose_name='Заказ',
        related_name='order_items')
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Товар',
        related_name='order_items')
    quantity = models.PositiveIntegerField('Количество', default=0)
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Продавец',
        related_name='+')


class Order(models.Model):
    STATUSES = (
        ('accepted', 'Принят'),
        ('confirmed', 'Подтверждён'),
        ('sent', 'Отправлен'),
        ('complete', 'Выполнен'),
        ('cancelled', 'Отменён'),
    )
    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Клиент',
        related_name='orders')
    items = models.ManyToManyField(
        Product,
        through=OrderItem, through_fields=('order', 'product'),
        verbose_name='Позиции заказа')
    status = models.CharField('Статус заказа', max_length=9, choices=STATUSES)

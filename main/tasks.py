import os

from django.core.mail import EmailMessage

from config.django_celery import app
from main.models import Pricelist, Category, Brand, PricelistFile, Product, Variant, Property, Order
from main.utils import get_totals


@app.task
def parse_pricelist(instance_id):
    def validate_upload_format(line_number, items):
        # Если кол-во "столбцов" чётное - значит не заполнены какие-то поля характеристик
        if len(items) % 2 == 0:
            return {
                'line': line_number,
                'detail': 'wrong column count (not enough `characteristic-value` pairs)'
            }
        # Маппинг столбцов по типу данных (кроме характеристик)
        index_type_map = {
            0: [str, 'category title'],
            1: [str, 'brand name'],
            2: [str, 'product model'],
            3: [str, 'product sku'],
            4: [int, 'in_stock'],
            5: [int, 'price'],
            6: [int, 'delivery price']
        }

        for ix, item in enumerate(items[:7]):
            item_type = index_type_map[ix][0]
            item_field = index_type_map[ix][1]

            try:
                item_value = int(item)
            except ValueError:
                item_value = item

            if not isinstance(item_value, item_type):
                return {
                    'line': line_number,
                    'value': item,
                    'detail': f'Field `{item_field}` (index {ix}) must be of type {item_type}'
                }
        return None

    file = PricelistFile.objects.get(pk=instance_id)
    # Значение по-умолчанию - выгрузка успешна, если в процессе не будет ошибок
    file.upload_result = {'status': 'parsed successfully'}
    seller = file.seller
    path = os.path.join(file.file.name)
    with open(path) as f:
        for line_number, line in enumerate(f.readlines()[1:]):
            items = line.split(',')
            # Валидация строки файла на соответствие формату
            error = validate_upload_format(line_number + 1, items)
            if error:
                file.upload_result = {'error': error}
                file.save()
                break
            category, _ = Category.objects.get_or_create(title=items[0].lower().strip())
            brand, _ = Brand.objects.get_or_create(title=items[1].lower().strip())
            product, _ = Product.objects.get_or_create(
                category=category, brand=brand, title=items[2].lower().strip()
            )
            sku = items[3].strip()
            variant, _ = Variant.objects.get_or_create(sku=sku, product=product)
            pl = Pricelist.objects.filter(variant=variant, seller=seller).first()
            if not pl:
                pl = Pricelist.objects.create(variant=variant, seller=seller)
            pl.in_stock = items[4]
            pl.product_price = items[5]
            pl.delivery_price = items[6]
            pl.save()
            # Создаём записи с парами: название характеристики - значение
            for ind in range(7, len(items), 2):
                prop, _ = Property.objects.get_or_create(
                    title=items[ind].lower().strip(), value=items[ind + 1].lower().strip())
                variant.props.add(prop)
    # Удаляем файл после парсинга
    file.file.delete()
    file.save()


@app.task
def send_order_info(mail):
    EmailMessage(**mail).send()


@app.task
def send_order_emails(order_id):
    order = Order.objects.get(pk=order_id)

    # Подготовка и отправка email покупателю о приёме заказа
    order_details = []
    for ix, item in enumerate(order.order_items.all()):
        order_details.append(
            f'{ix+1}. {str(item.pricelist.variant)}, '
            f'количество: {item.quantity}шт., '
            f'цена: {item.pricelist.product_price}, '
            f'стоимость доставки: {item.pricelist.delivery_price * item.quantity}'
        )
    order_details = '\n  '.join(order_details)
    products_total, delivery_total = get_totals(order.order_items.all())
    mail_to_customer = {
        'subject': f'Заказ №{order.id}',
        'body': f'  Здравствуйте! Вы оформили заказ.\n'
                f'Заказ №{order.id}\n'
                f'Дата и время оформления: {order.created_at.strftime("%Y/%m/%d %H:%S")}\n'
                f'Состав заказа:\n'
                f'  {order_details}\n'
                f'Итоговая сумма: {products_total + delivery_total}\n\n'
                f'Статус заказа можно узнать по ссылке:\n'
                f'  http://localhost:8000/orders/{order.id}/',
        'to': [order.customer.email]
    }
    send_order_info.delay(mail_to_customer)

    # Подготовка и отправка email о поступившем заказе для продавцов только с их товарами
    seller_email_list = [item.pricelist.seller.email for item in order.order_items.all()]
    message_queue = {email: {} for email in set(seller_email_list)}

    for ix, item in enumerate(order.order_items.all()):
        order_info = {
            'order_id': order.id,
            'customer': order.customer,
            'address': order.address
        }
        if message_queue[item.pricelist.seller.email] == {}:
            message_queue[item.pricelist.seller.email] = order_info
        product = {
            'product': str(item.pricelist.variant),
            'sku': item.pricelist.variant.sku,
            'price': item.pricelist.product_price,
            'quantity': item.quantity
        }

        if 'products' not in message_queue[item.pricelist.seller.email].keys():
            message_queue[item.pricelist.seller.email].update({'products': [product]})
        else:
            message_queue[item.pricelist.seller.email]['products'].append(product)

    for email in seller_email_list:
        order_data = message_queue[email]
        order_details = {
            'Заказ №': order_data['order_id'],
            'Покупатель': ' '.join([str(order_data['customer']), order_data['customer'].email]),
            'Компания': order_data['customer'].company,
            'Адрес доставки': order_data['address'],
            'Товары': '\n'.join([
                f'{ix+1}. {item["product"]} Цена: {item["price"]}, '
                f'кол-во: {item["quantity"]}'
                for ix, item in enumerate(order_data['products'])
            ])
        }
        mail_to_seller = {
            'subject': 'Поступил заказ',
            'body': f'Здравствуйте! Вам поступил заказ.\n'
                    f'{order_details}',
            'to': [email]
        }
        send_order_info.delay(mail_to_seller)

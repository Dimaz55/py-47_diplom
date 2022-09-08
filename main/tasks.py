import os

from config.django_celery import app
from main.models import Pricelist, Category, Brand, PricelistFile, Product, Variant, Property


@app.task
def parse_pricelist(instance_id):
    def validate_upload_format(line_number, items):
        if len(items) % 2 == 0:
            return {
                'line': line_number,
                'detail': 'wrong column count (not enough `characteristic-value` pairs)'
            }

        index_type_map = {
            0: [str, 'category title'],
            1: [str, 'brand name'],
            2: [str, 'product model'],
            3: [str, 'product sku'],
            4: [int, 'quantity'],
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
    file.upload_result = {'status': 'parsed successfully'}
    seller = file.seller
    path = os.path.join(file.file.name)
    with open(path) as f:
        for line_number, line in enumerate(f.readlines()[1:]):
            items = line.split(',')
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
            pl.quantity = items[4]
            pl.product_price = items[5]
            pl.delivery_price = items[6]
            pl.orderable = True if int(items[4]) > 0 else False
            pl.save()

            for ind in range(7, len(items), 2):
                prop, _ = Property.objects.get_or_create(
                    title=items[ind].lower().strip(), value=items[ind + 1].lower().strip())
                variant.props.add(prop)
    file.file.delete()
    file.save()

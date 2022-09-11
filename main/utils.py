from django.db.models import Sum, F


def get_totals(items):
    products = items.aggregate(pr=Sum(F('pricelist__product_price') * F('quantity')))['pr']
    delivery = items.aggregate(dl=Sum(F('pricelist__delivery_price') * F('quantity')))['dl']
    return products, delivery

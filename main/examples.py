from django.utils import timezone

BUYER_ORDER_LIST = {
    'id': 0,
    'status': 'string',
    'address': 'string',
    'summary': {
        'products_total': 0,
        'delivery_total': 0,
        'total': 0
    }
}

SELLER_ORDER_LIST = {
    'id': 0,
    'status': 'string',
    'address': 'string',
    'customer': 'string',
    'customer_company': 'string',
    'summary': {
        'products_total': 0,
        'delivery_total': 0,
        'total': 0
    }
}

BUYER_ORDER_DETAIL = {
    'id': 0,
    'status': 'string',
    'address': 'string',
    'created_at': timezone.now(),
    'items': [
        {
            'pricelist': 0,
            'product': 'string',
            'product_price': 0,
            'delivery_price': 0,
            'quantity': 0,
            'seller': 'string'
        }
    ],
    'summary': {
        'products_total': 0,
        'delivery_total': 0,
        'total': 0
    }
}

SELLER_ORDER_DETAIL = {
    'id': 0,
    'status': 'string',
    'address': 'string',
    'created_at': timezone.now(),
    'customer': 'string',
    'customer_company': 'string',
    'items': [
        {
            'pricelist': 0,
            'product': 'string',
            'sku': 'string',
            'product_price': 0,
            'delivery_price': 0,
            'quantity': 0,
            'in_stock': 0
        }
    ],
    'summary': {
        'products_total': 0,
        'delivery_total': 0,
        'total': 0
    }
}

CART_CONTENTS = {
    'id': 0,
    'summary': {
        'products_total': 0,
        'delivery_total': 0
    },
    'items': [
        {
            'pricelist': 0,
            'product': 'string',
            'product_price': 0,
            'delivery_price': 0,
            'quantity': 0,
            'seller': 'string'}
    ],
    'address': 'string'
}



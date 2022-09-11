from rest_framework.permissions import BasePermission

from main.models import Order


class IsSeller(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == 'seller')


class IsBuyer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.role == 'buyer')


class OrderPermission(BasePermission):
    def has_permission(self, request, view):
        is_auth = request.user.is_authenticated
        # Создание заказов доступно только покупателям
        if view.action == 'create':
            return is_auth and request.user.role == 'buyer'
        # Изменения статусов доступно только продавцам
        elif view.action in ['update', 'partial_update']:
            return is_auth and request.user.role == 'seller'
        elif view.action in ['retrieve', 'list']:
            return is_auth
        else:
            return False

    def has_object_permission(self, request, view, obj):
        is_auth = request.user.is_authenticated
        if not is_auth:
            return False
        
        is_seller = bool(request.user.role == 'seller')
        seller_orders = Order.objects.filter(items__seller=request.user) if is_seller else None
        
        if view.action == 'retrieve':
            return obj.customer == request.user or is_seller and obj in seller_orders
        elif view.action in ['update', 'partial_update'] and is_seller and obj in seller_orders:
            return True
        elif view.action == 'destroy':
            # Может-ли кто-то вообще удалять заказы?
            return request.user.is_admin
        else:
            return False

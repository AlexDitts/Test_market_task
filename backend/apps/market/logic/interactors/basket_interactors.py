import datetime
import pgbulk
import pytz
import requests
from django.conf import settings
from django.core.mail import send_mail

from django.db.models import F, QuerySet, Sum, Q
from rest_framework.serializers import ModelSerializer

from apps.content.models import RecipientEmail
from apps.credentials.models import EmailCredentials
from apps.market.enum import ShippingMethod
from apps.market.logic.selectors.basket_viewset_selectors import basket_daily_info_selector

from apps.market.models import Basket, ItemBasket
from utils.exeption import BusinessLogicException


def clear__payment_method__when__changed__delivery_method__or__address_data(
        *, serializer: ModelSerializer
) -> None:
    if (
            serializer.instance.payment_method
            or serializer.validated_data.get("payment_method")
    ) and (
            serializer.validated_data.get("city")
            or serializer.validated_data.get("country")
            or serializer.validated_data.get("delivery_method")
    ):
        if (
                serializer.instance.city != serializer.validated_data.get("city")
                or serializer.instance.country != serializer.validated_data.get("country")
                or serializer.instance.delivery_method
                != serializer.validated_data.get("delivery_method")
        ):
            serializer.validated_data.update(
                {"payment_method": None, "delivery_price": 0.0}
            )


def fixed__item_basket__when_accept(*, item_baskets: QuerySet[ItemBasket], basket) -> None:
    fixed_items = [
        ItemBasket(
            id=item.id,
            code=item.variant_product.code,
            name=item.variant_product.name,
            price=item.variant_product.price,
            sale_price=item.variant_product.sale_price,
            item_total_cost=item.variant_product.price * item.quantity,
            item_total_cost_with_discount=item.variant_product.sale_price
                                          * item.quantity,
            item_discount=(
                              (item.variant_product.price - item.variant_product.sale_price)
                              if item.variant_product.sale_price
                              else 0
                          )
                          * item.quantity,
            basket_id=basket.id,
        )
        for item in item_baskets
    ]
    update_fields = (
        "id",
        "code",
        "name",
        "price",
        "sale_price",
        "item_total_cost",
        "item_total_cost_with_discount",
        "item_discount",
        "basket_id",
    )
    pgbulk.update(ItemBasket, fixed_items, update_fields=update_fields)


def checking__products__to_order(*, basket: Basket) -> bool:
    """
    Проверяет есть ли в корзине товары под заказ с количеством большим чем доступно.
    """
    products_to_order = basket.item_baskets.filter(
        Q(quantity__gt=F('variant_product__quantity'))
        & Q(variant_product__to_order=True)
    ).exists()
    return products_to_order


def check_another_variants(*, item: ItemBasket) -> bool:
    product = item.variant_product.product
    return product.variants.filter(Q(quantity__gt=0) | Q(to_order=True)).exists()


def basket_order__generate_basket_items_string(
        *, item_baskets: QuerySet[ItemBasket]
) -> tuple[str, int]:
    items = ''
    items_cost = 0
    for item in item_baskets:
        items += (f'Название товара: {item.name}\n'
                  f'Количество: {item.quantity}\n'
                  f'Цена: {item.price if item.sale_price == 0.00 else item.sale_price}\n'
                  f'Итого: '
                  f'{item.price * item.quantity if item.sale_price == 0.00 else item.sale_price * item.quantity}\n\n')
        items_cost += item.price * item.quantity if item.sale_price == 0.00 else item.sale_price * item.quantity

    return items, items_cost

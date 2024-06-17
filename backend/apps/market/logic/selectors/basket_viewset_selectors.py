from datetime import datetime
from decimal import Decimal

from django.db.models import Q, QuerySet
from rest_framework.exceptions import ValidationError

from apps.market.constants import BASKET_WRONG_PK
from apps.market.enum import PaymentMethod, PaymentStatus, BasketStatus
from apps.market.models import Basket, ItemBasket
from apps.shipping_and_payment.models import PaymentVariant


def items__all() -> QuerySet[ItemBasket]:
    return ItemBasket.objects.all()


def items__by_basket(
    *, basket: Basket, qs: QuerySet[ItemBasket] = None
) -> QuerySet[ItemBasket]:
    if qs is None:
        qs = items__all()
    return qs.filter(basket=basket)


def baskets__all() -> QuerySet[Basket]:
    return Basket.objects.all()


def baskets__by_pk(*, pk: int, qs: QuerySet[Basket] | None = None) -> QuerySet[Basket]:
    if qs is None:
        qs = baskets__all()
    return qs.filter(pk=pk)


def basket__find_by_pk(*, pk: int, qs: QuerySet[Basket] | None = None) -> Basket | None:
    return baskets__by_pk(pk=pk, qs=qs).first()


def basket__get_or_raise_error(*, pk: int) -> Basket:
    basket = basket__find_by_pk(pk=pk)
    if not basket:
        raise ValidationError(BASKET_WRONG_PK)
    return basket


def basket_daily_info_selector(date: datetime.date) -> QuerySet[Basket]:
    return Basket.objects.filter(
        update_at__date=date,
        status=BasketStatus.COMPLETED
    ).exclude(
        payment_method=PaymentMethod.ONLINE,
        payment_status__in=[
            PaymentStatus.UNPAID,
            PaymentStatus.AWAITING_PAYMENT
        ]
    )

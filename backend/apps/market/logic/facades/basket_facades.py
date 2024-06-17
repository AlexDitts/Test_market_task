from django.core.management import BaseCommand
from structlog import get_logger

from apps.market.logic.selectors.basket_viewset_selectors import baskets__by_pk
from apps.market.models import Basket, ItemBasket
from utils.exeption import BusinessLogicException

logger = get_logger(__name__)


def check_order_parameters(*, basket: Basket) -> None:
    if not basket.customer_name or not basket.customer_surname:
        raise BusinessLogicException("Не заполнены данные заказчика")

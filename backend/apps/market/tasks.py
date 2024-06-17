import hashlib
from datetime import datetime

import requests
from django.db.models import Q
from structlog import get_logger

from apps.credentials.models import TinkoffCredentials
from apps.market.enum import PaymentMethod, PaymentStatus
from apps.market.logic.interactors.cdek import create_cdek_order
from apps.market.logic.selectors.basket_viewset_selectors import basket__find_by_pk
from apps.market.models import Basket, Product
from config.celery import app

logger = get_logger(__name__)


@app.task(name="Обработка платежа")
def payment_reaction(basket_id: int, token) -> None:
    basket = Basket.objects.get(pk=basket_id)
    tinkoff = TinkoffCredentials.get_solo()
    response = requests.post(
        url="https://securepay.tinkoff.ru/v2/GetState",
        json={
            "TerminalKey": tinkoff.terminal_key,
            "Token": hashlib.sha256(
                "".join(
                    [tinkoff.terminal_pass, basket.payment_id, tinkoff.terminal_key]
                ).encode("utf-8")
            ).hexdigest(),
            "PaymentId": basket.payment_id,
        },
    )
    state_data = response.json()
    if state_data['Status'] != 'CONFIRMED':
        basket.token = token
        basket.save()
    if basket.payment_status != PaymentStatus.PAID and state_data['Status'] == 'CONFIRMED':
        basket.payment_status = PaymentStatus.PAID
        basket.save()


@app.task(name='Выбор товаров по полю "characteristics__value"')
def get_products__by__characteristics_value(value):
    products = list(Product.objects.filter(characteristics__value__icontains=value).values_list('id', flat=True))
    return {'data': products}


@app.task(name='Выбор по полю "id"')
def get_products__by__id(value):
    products = list(Product.objects.filter(id__icontains=value).values_list('id', flat=True))
    return {'data': products}


@app.task(name='Выбор по полю "name"')
def get_products__by__name(value):
    products = list(Product.objects.filter(Q(name__icontains=value)).values_list('id', flat=True))
    return {'data': products}


@app.task(name='Выбор по полю '"code"'')
def get_products__by__code(value):
    products = list(Product.objects.filter(code__icontains=value).values_list('id', flat=True))
    return {'data': products}


@app.task(name='Выбор по полю '"article"'')
def get_products__by__article(value):
    products = list(Product.objects.filter(article__icontains=value).values_list('id', flat=True))
    return {'data': products}


@app.task(name='Выбор по полю '"description"'')
def get_products__by__description(value):
    products = list(Product.objects.filter(Q(description__icontains=value)).values_list('id', flat=True))
    return {'data': products}


@app.task(name='Выбор по полю '"brand__name"'')
def get_products__by__brand__name(value):
    products = list(Product.objects.filter(Q(brand__name__icontains=value)).values_list('id', flat=True))
    return {'data': products}


@app.task(name='Выбор по полю '"variants__code"'')
def get_products__by__variants__code(value):
    products = list(Product.objects.filter(variants__code__icontains=value).values_list('id', flat=True))
    return {'data': products}


@app.task(name='Отправка ежедневного отчёта по заказам')
def send__daily_order_information_to_email__task():
    send_daily_order_information_to_email()


@app.task(name='Обновление файла для яндекс поиска')
def update__yandexfeed_file() -> None:
    write__yandex_feed_file(data=collect_data__to_yandex_feed())

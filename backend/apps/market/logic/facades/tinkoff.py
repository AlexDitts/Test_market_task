import hashlib
from uuid import UUID

import requests
from django.db import transaction

from apps.credentials.models import TinkoffCredentials
from apps.market.logic.interactors.tinkoff import (
    basket__check_payment,
    basket__create_payment_data_and_actualise_basket,
    check_basket__is_accept,
    check_basket__is_online_payment,
)
from apps.market.models import Basket
from utils.uri import protocol_with_domain_uri__convert


def basket__check_payment_and_verify_payer(
        *, basket: Basket, token: UUID, request_absolute_uri: str
) -> None:
    basket__check_payment(basket=basket)

    # protocol_with_domain_uri = protocol_with_domain_uri__convert(
    #     absolute_uri=request_absolute_uri
    # )
    # TODO: уточнить, что писать пользователю на успешную оплату заказа
    # NOTE: При рендере HTML не работает STATIC все линки работают на domain переменной
    # message_data = {
    #     "from_email": EmailCredentials.get_solo().default_from_email,
    #     "subject": "Заказ оплачен",
    #     "body": "Добрый день!",
    #     "to": [basket.customer_email or basket.user.email],
    #     "headers": {"Message-ID": "gksport-success-payment"},
    #     # "html_content": render_to_string(
    #     #     # Возможно сверстать email
    #     #     "some_email.html",
    #     #     {"domain": protocol_with_domain_uri},
    #     # ),
    # }
    # message_data_dto = EmailMultiAlternativesDto(**message_data)
    # email_multi_alternatives__send(message_data_dto=message_data_dto)


@transaction.atomic
def basket_payment_url(
        *,
        basket: Basket,
        absolute_uri: str,
        payment_success_url: str,
        payment_fail_url: str,
) -> str:
    """
    Обрабатывает данные платежа и отправляет ссылку на указанную почту.

    params: basket: экземпляр класса Basket,
    params: request_uri - ссылка в формате http://localhost:8000/api/baskets/41/send_payment_url/

    return: str:
    """
    if basket.payment_id:
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
        if state_data['Status'] != 'CANCELED':
            return basket.payment_url
    protocol_with_domain_uri = protocol_with_domain_uri__convert(
        absolute_uri=absolute_uri
    )
    check_basket__is_accept(basket=basket)
    check_basket__is_online_payment(basket=basket)
    payment_data = basket__create_payment_data_and_actualise_basket(
        basket=basket,
        protocol_with_domain_uri=protocol_with_domain_uri,
        payment_success_url=payment_success_url,
        payment_fail_url=payment_fail_url,
    )
    return payment_data.payment_url

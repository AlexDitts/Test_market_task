import hashlib
import uuid

import requests
from django.urls import reverse
from restdoctor.rest_framework.exceptions import BadRequest
from structlog import get_logger

from apps.credentials.models import TinkoffCredentials
from apps.market.constants import (KOPECKS_IN_RUB,
                                   TINKOFF_PAYMENT_CANT_BE_CANCELED,
                                   TINKOFF_PAYMENT_CANT_BE_PROVIDE,
                                   TINKOFF_PAYMENT_HAS_NOT_EMAIL,
                                   TINKOFF_PAYMENT_INCORRECT_TOKEN,
                                   TINKOFF_PAYMENT_NOT_EXISTS,
                                   TINKOFF_PAYMENT_OSN_TAXATION)
from apps.market.dto.tinkoff import (TinkoffPaymentDto, TinkoffPaymentItemDto,
                                     TinkoffPaymentResponseDto)
from apps.market.enum import BasketStatus, PaymentMethod, PaymentStatus
from apps.market.logic.selectors.basket_viewset_selectors import \
    items__by_basket
from apps.market.models import Basket
from apps.market.utils import tinkoff_payment__generate_token
from utils.exeption import BusinessLogicException
from utils.model import update_model_instance


def check_basket__is_accept(*, basket: Basket) -> None:
    if basket.status != BasketStatus.COMPLETED.value:
        raise BusinessLogicException(TINKOFF_PAYMENT_CANT_BE_PROVIDE)


def check_basket__is_online_payment(*, basket: Basket) -> None:
    if basket.payment_method != PaymentMethod.ONLINE.value:
        raise BusinessLogicException(TINKOFF_PAYMENT_CANT_BE_PROVIDE)


logger = get_logger(__name__)


def basket__payment_items(*, basket: Basket) -> list[TinkoffPaymentItemDto]:  # --------
    """
    :param basket: корзина МСП
    :return: список данных о платеже в виде TinkoffPaymentItemsDto
    """
    payment_items = []
    items = items__by_basket(basket=basket)
    items_list = items.values_list(
        "item_total_cost_with_discount",
        "item_total_cost",
        "price",
        "sale_price",
        "name",
        "quantity",
    )
    all_items_price = 0
    for (
        total_cost_discount,
        total_cost,
        price,
        sale_price,
        name,
        quantity,
    ) in items_list:
        price = (sale_price or price) * KOPECKS_IN_RUB
        total_cost = (total_cost_discount or total_cost) * KOPECKS_IN_RUB
        all_items_price += total_cost
        payment_item_data = {
            "Name": name,
            "Price": price,
            "Quantity": quantity,
            "Amount": total_cost,
            "PaymentMethod": "full_payment",
            "PaymentObject": "commodity",
            "Tax": "none",
        }
        dto = TinkoffPaymentItemDto(**payment_item_data)
        payment_items.append(dto)
    delivery_price = (
        basket.delivery_price or basket.delivery_method.price
    ) * KOPECKS_IN_RUB
    payment_items.append(
        {
            "Name": "Доставка",
            "Price": delivery_price,
            "Quantity": 1,
            "Amount": delivery_price,
            "PaymentMethod": "full_payment",
            "PaymentObject": "service",
            "Tax": "none",
        }
    )

    logger.info("Стоимость доставки " + str(delivery_price))
    logger.info("Стоимость товаров " + str(all_items_price))
    logger.info(
        "Сумма всей корзины с доставкой в копейках "
        + str(all_items_price + delivery_price)
    )
    return payment_items


def basket__generate_payment_data(
    *,
    basket: Basket,
    protocol_with_domain_uri: str,
    notification_token: uuid.UUID,
    payment_success_url: str,
    payment_fail_url: str,
) -> TinkoffPaymentDto:
    tinkoff = TinkoffCredentials.get_solo()
    total_cost_in_rubles = basket.total_cost
    phone_number = (
        basket.customer_phone if basket.customer_phone else basket.user.username
    )
    email = basket.customer_email if basket.customer_email else basket.user.email
    receipt_data = {
        "Email": email,
        "Taxation": "usn_income",
        "Items": basket__payment_items(basket=basket),
        "Phone": phone_number,
    }
    logger.info(
        "Итоговая стоимость корзины " + str(total_cost_in_rubles * KOPECKS_IN_RUB)
    )
    payment_data = {
        "TerminalKey": tinkoff.terminal_key,
        "Amount": total_cost_in_rubles * KOPECKS_IN_RUB,
        "OrderId": f"{basket.order_name}\n({basket.order_number})",
        # NOTE: Возможно заказчик попросит другое сообщение
        "Description": f"Товары на общую сумму {total_cost_in_rubles} руб.",
        "NotificationURL": protocol_with_domain_uri
        + reverse("basket-check-payment-and-inform", kwargs={"pk": basket.pk})
        + f"?token={notification_token}",
        "DATA": {"Phone": phone_number, "Email": email},
        "Receipt": receipt_data,
    }
    logger.info(f'{payment_data.get("OrderId")}')
    if tinkoff.payment_success_url or payment_success_url:
        payment_data["SuccessURL"] = payment_success_url or tinkoff.payment_success_url
    if tinkoff.payment_fail_url or payment_fail_url:
        payment_data["FailURL"] = payment_fail_url or tinkoff.payment_fail_url
    payment_dto_without_token = TinkoffPaymentDto(**payment_data)
    payment_data["Token"] = tinkoff_payment__generate_token(
        payment_dto=payment_dto_without_token
    )
    return TinkoffPaymentDto(**payment_data)


def tinkoff__init_payment(
    *, payment_dto: TinkoffPaymentDto
) -> TinkoffPaymentResponseDto:
    """
    Документация API - https://www.tinkoff.ru/kassa/dev/payments/ .
    """
    response = requests.post(
        url="https://securepay.tinkoff.ru/v2/Init",
        json=payment_dto.dict(exclude_unset=True, by_alias=True),
    )
    payment_data = response.json()
    if not payment_data.get("PaymentURL"):
        raise BadRequest(
            f'Не удалось получить ссылку на оплату. {payment_data.get("Details", "")}'
        )
    if not payment_data.get("PaymentId"):
        raise BadRequest(
            f'Не удалось получить уникальный номер платежа. {payment_data.get("Details", "")}'
        )
    return TinkoffPaymentResponseDto(**payment_data)


def tinkoff__cancel_payment(*, payment_id: str):
    """
    Документация API - https://www.tinkoff.ru/kassa/dev/payments/.
    """
    tinkoff = TinkoffCredentials.get_solo()
    response = requests.post(
        url="https://securepay.tinkoff.ru/v2/Cancel",
        json={
            "TerminalKey": tinkoff.terminal_key,
            "Token": hashlib.sha256(
                "".join(
                    [tinkoff.terminal_pass, payment_id, tinkoff.terminal_key]
                ).encode("utf-8")
            ).hexdigest(),
            "PaymentId": payment_id,
        },
    )
    payment_data = response.json()
    if not payment_data["Success"]:
        raise BusinessLogicException(TINKOFF_PAYMENT_CANT_BE_CANCELED)


# def tinkoff__cancel_payment(*, payment_id: str):
#     """
#     Документация API - https://www.tinkoff.ru/kassa/dev/payments/.
#     """
#     tinkoff = TinkoffCredentials.get_solo()
#     response = requests.post(
#         url="https://securepay.tinkoff.ru/v2/Cancel",
#         json={
#             "TerminalKey": tinkoff.terminal_key,
#             "Token": hashlib.sha256(
#                 "".join(
#                     [tinkoff.terminal_pass, payment_id, tinkoff.terminal_key]
#                 ).encode("utf-8")
#             ).hexdigest(),
#             "PaymentId": payment_id,
#         },
#     )
#     payment_data = response.json()
#     if not payment_data["Success"]:
#         raise BusinessLogicException(TINKOFF_PAYMENT_CANT_BE_CANCELED)


def basket_payment_status__change_to_awaiting_payment(
    *, basket: Basket, payment_id: str, token: uuid.UUID, payment_url: str
) -> Basket:
    """
    При отправке ссылки на оплату корзины:
    2)обновляется сущность корзины ключом payment_id = id платежа и token для верификации запроса,
    """

    validated_data = {
        "payment_id": payment_id,
        "token": token,
        "payment_status": PaymentStatus.AWAITING_PAYMENT,
        "payment_url": payment_url,
    }
    return update_model_instance(
        instance=basket,
        validated_data=validated_data,
        update_fields=["payment_id", "token", "payment_status", "payment_url"],
    )


def basket__create_payment_data_and_actualise_basket(
    basket: Basket,
    protocol_with_domain_uri: str,
    payment_success_url: str,
    payment_fail_url: str,
) -> TinkoffPaymentResponseDto:
    token = uuid.uuid4()
    payment_data = tinkoff__init_payment(
        payment_dto=basket__generate_payment_data(
            basket=basket,
            notification_token=token,
            protocol_with_domain_uri=protocol_with_domain_uri,
            payment_fail_url=payment_fail_url,
            payment_success_url=payment_success_url,
        )
    )

    basket_payment_status__change_to_awaiting_payment(
        basket=basket,
        payment_id=payment_data.payment_id,
        token=token,
        payment_url=payment_data.payment_url,
    )

    return payment_data


def basket_payment_status__change_to_paid(*, basket: Basket) -> None:
    update_model_instance(
        instance=basket,
        validated_data={
            "token": None,
            # "payment_status": PaymentStatus.PAID,
            "payment_url": None,
        },
        update_fields=["token", "payment_status", "payment_url"],
    )


def basket__check_payment(*, basket: Basket) -> None:
    basket_payment_status__change_to_paid(basket=basket)

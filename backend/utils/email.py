import smtplib
import socket
from typing import Any

from django.core.mail import EmailMultiAlternatives

from apps.market.constants import NOT_ANY_SENT_MESSAGES
from utils.dto import EmailMultiAlternativesDto
from utils.exeption import BusinessLogicException


def email_multi_alternatives__send(
    *,
    message_data_dto: EmailMultiAlternativesDto,
    content_type: str = "text/html",
    connection: Any | None = None,
) -> int:
    message_data = message_data_dto.dict()
    if not message_data_dto.attachments:
        message_data.pop("attachments")
    if connection:
        message_data["connection"] = connection
    html_content = message_data.pop("html_content", "")
    try:
        email_message = EmailMultiAlternatives(**message_data)
        email_message.attach_alternative(html_content, content_type)
        email_messages_count = email_message.send()
        if not email_messages_count:
            raise BusinessLogicException(NOT_ANY_SENT_MESSAGES)
        return email_messages_count

    except (
        smtplib.SMTPServerDisconnected,
        smtplib.SMTPDataError,
        socket.gaierror,
    ) as error:
        raise BusinessLogicException(f"{error}")

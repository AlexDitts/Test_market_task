from typing import Iterable, TypeVar

from django.db.models import Model
from pydantic import BaseModel


class BaseDto(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        allow_mutation = False
        use_enum_values = True
        orm_mode = True


BaseDtoTyping = TypeVar("BaseDtoTyping", bound=BaseDto)
DjangoModel = TypeVar("DjangoModel", bound=Model)


class CommonEmailMessageDto(BaseDto):
    subject: str
    from_email: str
    to: Iterable[str] | str
    attachments: list[tuple[str, bytes, str]] | None
    body: str


class EmailMessageSendingDto(CommonEmailMessageDto):
    headers: dict


class EmailMultiAlternativesDto(CommonEmailMessageDto):
    html_content: str = ""

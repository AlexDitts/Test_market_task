from pydantic import Json, Extra

from apps.user.enum import DadataActions
from utils.dto import BaseDto


class DadataRequestBody(BaseDto, extra=Extra.allow):
    query: str


class DadataDto(BaseDto):
    endpoint: str
    action: DadataActions
    body: Json[DadataRequestBody]


class DadataResponseDto(BaseDto):
    data: dict | list[dict] | None

from pydantic import Field

from utils.dto import BaseDto


class CommonTerminalInitDto(BaseDto):
    pass


class AbstractPaymentResponseDto(BaseDto):
    pass


class TinkoffTerminalInitDto(CommonTerminalInitDto):
    key: str
    payment_success_url: str
    payment_failure_url: str


class SeparatedPriceInStringDto(BaseDto):
    rubbles: str
    kopecks: str


class TinkoffPaymentItemDto(BaseDto):
    name: str = Field(alias="Name")
    price: int = Field(alias="Price")
    quantity: int = Field(alias="Quantity")
    amount: int = Field(alias="Amount")
    payment_method: str | None = Field(alias="PaymentMethod")
    payment_object: str | None = Field(alias="PaymentObject")
    tax: str = Field(alias="Tax")


class TinkoffPaymentDataDto(BaseDto):
    phone: str | None = Field(alias="Phone")
    email: str | None = Field(alias="Email")


class TinkoffPaymentReceiptDto(TinkoffPaymentDataDto):
    taxation: str = Field(alias="Taxation")
    items: list[TinkoffPaymentItemDto] = Field(alias="Items")


class TinkoffPaymentUrlsDto(AbstractPaymentResponseDto):
    success_url: str | None = Field(alias="SuccessURL")
    fail_url: str | None = Field(alias="FailURL")


class TinkoffPaymentDto(TinkoffPaymentUrlsDto):
    data: TinkoffPaymentDataDto = Field(alias="DATA")
    terminal_key: str = Field(alias="TerminalKey")
    amount: int = Field(alias="Amount")
    order_id: str = Field(alias="OrderId")
    description: str = Field(alias="Description")
    receipt: TinkoffPaymentReceiptDto = Field(alias="Receipt")
    notification_url: str = Field(alias="NotificationURL")
    token: str | None = Field(alias="Token")


class TinkoffPaymentResponseDto(BaseDto):
    terminal_key: str | None = Field(alias="TerminalKey")
    amount: int | None = Field(alias="Amount")
    order_id: str | None = Field(alias="OrderId")
    success: bool = Field(alias="Success")
    status: str | None = Field(alias="Status")
    payment_id: str = Field(alias="PaymentId")
    error_code: str = Field(alias="ErrorCode")
    payment_url: str = Field(alias="PaymentURL")
    message: str | None = Field(alias="Message")
    details: str | None = Field(alias="Details")

from django.contrib import admin, messages
from django.core.handlers.wsgi import WSGIRequest
from django.forms import Form

from apps.credentials.admin.forms import (
    EmailCredentialsForm,
    SMSRuCredentialsForm,
)
from apps.credentials.models import (
    EmailCredentials,
    SMSRuCredentials,
    TinkoffCredentials,
)
from utils.abstractions.admin import AbstractSoloAdmin


@admin.register(SMSRuCredentials)
class SMSRuCredentialsAdmin(AbstractSoloAdmin):
    form = SMSRuCredentialsForm
    list_display = ("sender", "test")
    fieldsets = (
        (
            "Общее",
            {
                "fields": (
                    "sender",
                    "test",
                    "api_id",
                    "login",
                    "password",
                )
            },
        ),
    )

    def save_model(
        self, request: WSGIRequest, obj: SMSRuCredentials, form: Form, change: bool
    ) -> None:
        super().save_model(request=request, obj=obj, form=form, change=change)
        self.message_user(
            request=request, level=messages.SUCCESS, message="SMS.ru изменён (^˵◕ω◕˵^)"
        )


@admin.register(EmailCredentials)
class EmailCredentialsAdmin(AbstractSoloAdmin):
    form = EmailCredentialsForm
    list_display = ("host", "host_user")
    fieldsets = (
        (
            "Общее",
            {
                "fields": (
                    "host",
                    "port",
                    "use_tls",
                    "use_ssl",
                    "host_user",
                    "host_password",
                    "default_from_email",
                )
            },
        ),
    )

    def save_model(
        self, request: WSGIRequest, obj: SMSRuCredentials, form: Form, change: bool
    ) -> None:
        super().save_model(request=request, obj=obj, form=form, change=change)
        self.message_user(
            request=request,
            level=messages.SUCCESS,
            message='Email изменён (^˵◕ω◕˵^), но советую перепроверить "Host e-mail" и "Host password"',
        )


@admin.register(TinkoffCredentials)
class TinkoffCredentialsAdmin(AbstractSoloAdmin):
    list_display = ("terminal_key",)
    fieldsets = (
        (
            "Общее",
            {
                "fields": (
                    "terminal_key",
                    "terminal_pass",
                    "payment_success_url",
                    "payment_fail_url",
                )
            },
        ),
    )

    def save_model(
        self, request: WSGIRequest, obj: TinkoffCredentials, form: Form, change: bool
    ) -> None:
        super().save_model(request=request, obj=obj, form=form, change=change)
        self.message_user(
            request=request,
            level=messages.SUCCESS,
            message="Тинькофф изменён (^˵◕ω◕˵^).",
        )

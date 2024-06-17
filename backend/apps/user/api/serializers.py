from typing import Any, Optional, Type

from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import AuthUser
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken, Token
from restdoctor.rest_framework.serializers import PydanticSerializer

from apps.market.api.serializers import ProductListSerializer
from apps.market.enum import BasketStatus
from apps.user.dto.dadata import DadataDto
from apps.user.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "number_in_favorites",
            "number_of_orders",
            "is_active",
            "date_joined",
            "products"
        )
        extra_kwargs = {
            "is_active": {"read_only": True, "required": False},
            "date_joined": {"read_only": True, "required": False},
        }
    number_in_favorites = serializers.SerializerMethodField()
    number_of_orders = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()

    def get_products(self, obj: User) -> list:
        return ProductListSerializer(obj.products.all(), many=True).data

    def get_number_in_favorites(self, obj: User) -> int:
        return obj.products.count()

    def get_number_of_orders(self, obj: User) -> int:
        return obj.baskets.exclude(status=BasketStatus.IS_ACTIVE).count()


class SignupOrLoginSerializer(serializers.Serializer):
    class Meta:
        fields = ("username",)

    username = serializers.CharField(help_text="Номер телефона пользователя")


class SMSCallbackSerializer(serializers.Serializer):
    class Meta:
        fields = ("username", "key")

    username = serializers.CharField(help_text="Номер телефона пользователя")
    key = serializers.IntegerField(help_text="Код из смс")


class ChangeUsenameSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('update_username', )


class DadataRequestSerializer(PydanticSerializer):
    class Meta:
        pydantic_model = DadataDto


class TokenObtainSerializer(serializers.Serializer):
    username_field = get_user_model().USERNAME_FIELD
    token_class: Optional[Type[Token]] = None

    default_error_messages = {
        "no_active_account": _("No active account found with the given credentials")
    }

    def __init__(self, user, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields[self.username_field] = serializers.CharField(write_only=True)

    def validate(self, attrs: dict[str, Any]) -> dict[Any, Any]:
        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
        }
        try:
            authenticate_kwargs["request"] = self.context["request"]
        except KeyError:
            pass
        if not api_settings.USER_AUTHENTICATION_RULE(self.user):
            raise AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

        return {}

    @classmethod
    def get_token(cls, user: AuthUser) -> Token:
        return cls.token_class.for_user(user)  # type: ignore


class TokenObtainPairSerializer(TokenObtainSerializer):
    token_class = RefreshToken

    def validate(self, attrs: dict[str, Any]) -> dict[str, str]:
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        return data

import random
from datetime import datetime, timedelta

import pytz
from django.conf import settings
from django.contrib.auth import login, logout
from rest_framework import exceptions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import AUTH_HEADER_TYPES
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from restdoctor.rest_framework import viewsets
from smsru.service import SmsRuApi

from apps.user.api.serializers import (ChangeUsenameSerializer,
                                       SignupOrLoginSerializer,
                                       SMSCallbackSerializer,
                                       TokenObtainPairSerializer,
                                       UserSerializer)


from apps.user.models import SMSKey, User
from utils import exeption
from utils.exeption import BusinessLogicException

timezone = pytz.timezone(settings.TIME_ZONE)


class UserViewSet(viewsets.ModelViewSet):
    serializer_class_map = {
        "default": UserSerializer,
        "signup_or_login": {"request": SignupOrLoginSerializer},
        "change_phone": {"request": ChangeUsenameSerializer},
        "sms_callback_for_username_change": {
            "request": SMSCallbackSerializer,
            "response": TokenObtainPairSerializer
        },
        "sms_callback": {
            "request": SMSCallbackSerializer,
            "response": TokenObtainPairSerializer,
        },
        "refresh": {"request": TokenRefreshSerializer},
    }
    www_authenticate_realm = "api"
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    def get_authenticate_header(self, request: Request) -> str:
        return '{} realm="{}"'.format(
            AUTH_HEADER_TYPES[0],
            self.www_authenticate_realm,
        )

    def list(self, request: Request, *args: tuple, **kwargs: dict) -> Response:
        return Response(
            self.get_serializer(request.user).data,
            content_type="application/json",
        )

    def retrieve(self, request: Request, *args: tuple, **kwargs: dict) -> Response:
        raise exceptions.NotFound()

    @action(methods=("post",), detail=False, permission_classes=[IsAuthenticated])
    def change_phone(self, request: Request) -> Response:
        key = random.randint(1000, 9999)
        user = request.user
        user.update_username = None
        user.save()
        if hasattr(user, 'sms_key'):
            user.sms_key.delete()
        try:
            request_serializer = self.get_request_serializer(data=request.data)
            request_serializer.is_valid(raise_exception=True)
            update_username = request_serializer.validated_data.get('update_username')
            if User.objects.filter(username=update_username).exists():
                raise BusinessLogicException('Пользователь с таким номером телефона уже существует')
        except ValidationError as ex:
            if ex.args[0].get('update_username')[0].code == 'invalid':
                raise BusinessLogicException('Введён некорректный номера телефона')
            raise BusinessLogicException('Пользователь с таким номером телефона уже существует')

        try:
            result = SmsRuApi().send_one_sms(update_username, f"Код для изменения номера телефона: {key}")
            if result[list(result.keys())[0]]["status"]:
                sms_key, _ = SMSKey.objects.get_or_create(user=user, key=key)
                sms_key.key = key
                sms_key.save()
                user.update_username = update_username
                user.save()
                return Response(
                    status=200,
                    data={"detail": "Сообщение отправлено"},
                )
            else:
                raise exeption.BusinessLogicException(
                    f'sms.ru: {result[list(result.keys())[0]]["status_text"]}',
                )
        except BaseException as _error:
            raise exeption.BusinessLogicException(
                f"system: {_error.__str__()}",
            )

    @action(methods=['post'], detail=False, permission_classes=[IsAuthenticated])
    def sms_callback_for_username_change(self, request: Request) -> Response:
        request_serializer = self.get_request_serializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        user = request.user
        key_value = request_serializer.validated_data.get('key')
        key = SMSKey.objects.filter(key=key_value, user=user).first()
        if key:
            user.username = user.update_username
            user.save()
            key.delete()
            login(
                request=request,
                user=user,
                backend="apps.user.auth_backend.PasswordlessAuthBackend",
            )
            response_serializer = self.get_response_serializer(
                data={
                    "username": user.username,
                },
                user=user,
            )
            response_serializer.is_valid(raise_exception=True)
            return Response(
                response_serializer.validated_data,
                status=200,
                content_type="application/json",
            )
        else:
            raise exeption.BusinessLogicException('Введён неверный код')

    @action(methods=["post"], detail=False, permission_classes=[AllowAny])
    def signup_or_login(self, request: Request) -> Response:
        if request.user.is_authenticated:
            raise exeption.BusinessLogicException("Вы уже авторизованны")
        try:
            key = random.randint(1000, 9999)
            request_serializer = self.get_request_serializer(data=request.data)
            request_serializer.is_valid(raise_exception=True)
            username = request_serializer.validated_data["username"]
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.save()
            if hasattr(user, "sms_key"):
                time_now = datetime.now(timezone)
                time_key = user.sms_key.update_at.astimezone(timezone)
                time_difference = time_now - time_key
                if time_difference < timedelta(seconds=60):
                    return Response(
                        data={
                            "detail": "Повторные запросы можно делать не чаще чем через одну минуту"
                        }
                    )
                else:
                    user.sms_key.delete()
            result = SmsRuApi().send_one_sms(username, f"Код авторизации: {key}")
            if result[list(result.keys())[0]]["status"]:
                sms_key, _ = SMSKey.objects.get_or_create(user=user, key=key)
                sms_key.key = key
                sms_key.save()
                return Response(
                    status=200,
                    data={"detail": "Сообщение отправлено"},
                )
            else:
                raise exeption.BusinessLogicException(
                    f'sms.ru: {result[list(result.keys())[0]]["status_text"]}',
                )
        except BaseException as _error:
            raise exeption.BusinessLogicException(
                f"system: {_error.__str__()}",
            )

    @action(methods=["post"], detail=False, permission_classes=[AllowAny])
    def sms_callback(self, request: Request) -> Response:
        if request.user.is_authenticated:
            raise exeption.BusinessLogicException("Вы уже авторизованны")
        try:
            request_serializer = self.get_request_serializer(data=request.data)
            request_serializer.is_valid(raise_exception=True)
            username = request_serializer.validated_data["username"]
            key_value = request_serializer.validated_data["key"]
            user = User.objects.filter(username=username).first()
            key = SMSKey.objects.filter(key=key_value).first()
            if user and key and key.user == user:
                login(
                    request=request,
                    user=user,
                    backend="apps.user.auth_backend.PasswordlessAuthBackend",
                )
                key.delete()
                serializer = self.get_response_serializer(
                    data={
                        "username": user.username,
                    },
                    user=user,
                )
                try:
                    serializer.is_valid(raise_exception=True)
                except TokenError as e:
                    raise InvalidToken(e.args[0])
                return Response(
                    serializer.validated_data,
                    status=200,
                    content_type="application/json",
                )
            else:
                raise exeption.BusinessLogicException("Неверный код")
        except BaseException as _error:
            raise exeption.BusinessLogicException(
                f"system: {_error.__str__()}",
            )

    @action(methods=["post"], detail=False, permission_classes=[AllowAny])
    def refresh(self, request: Request) -> Response:
        serializer = self.get_request_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        return Response(
            serializer.validated_data, status=200, content_type="application/json"
        )

    @action(methods=["post"], detail=False, permission_classes=[AllowAny])
    def logout(self, request: Request) -> Response:
        logout(request)
        return Response(status=200, data={}, content_type="application/json")

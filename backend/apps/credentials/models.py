from smtplib import SMTPAuthenticationError
from socket import gaierror
from ssl import SSLError

import requests
from django.conf import settings
from django.core import exceptions
from django.core.mail.backends.smtp import EmailBackend
from django.db import models
from structlog import get_logger

from utils.abstractions.model import AbstractBaseSoloModel

logger = get_logger(__name__)


class SMSRuCredentials(AbstractBaseSoloModel):
    class Meta:
        verbose_name = 'Данные для подключения SMS.ru'
        verbose_name_plural = 'Данные для подключения SMS.ru'

    api_id = models.CharField(
        verbose_name='API ключ',
        help_text='Если указан API ключ, логин и пароль пропускаем.',
        max_length=512,
        null=True,
        blank=True,
    )
    login = models.CharField(
        verbose_name='Логин',
        help_text='Если нет API ключа, то авторизуемся чезер логин и пароль.',
        max_length=512,
        null=True,
        blank=True,
    )
    password = models.CharField(
        verbose_name='Пароль',
        help_text='Если нет API ключа, то авторизуемся чезер логин и пароль.',
        max_length=512,
        null=True,
        blank=True,
    )
    test = models.BooleanField(
        verbose_name='Тестовый режим',
        help_text=(
            'Сообщения в тестом режиме не будут отправлены в действительности,'
            ' но в обоих сервисах будут созданы записи о них.'
        ),
        null=True,
        blank=True,
    )
    sender = models.CharField(
        verbose_name='Отправитель',
        help_text='Имя отображаемое при получении сообщения.',
        default='GKSport',
        null=True,
        blank=True,
    )

    def clean(self) -> None:
        url = 'https://sms.ru/auth/check?'
        if self.api_id:
            status = requests.get(
                f'{url}api_id={self.api_id}&json=1'
            ).json()['status'] == 'OK'
            if not status:
                raise exceptions.ValidationError(
                    message=(
                        'API ключ не найден (ಥ﹏ಥ)'
                    )
                )
        elif self.login and self.password:
            status = requests.get(
                f'{url}login={self.login}&password={self.password}&json=1'
            ).json()['status'] == 'OK'
            if not status:
                raise exceptions.ValidationError(
                    message=(
                        'Логин или пароль указан не верно (ಥ﹏ಥ)'
                    )
                )
        return super().clean()


class TinkoffCredentials(AbstractBaseSoloModel):
    class Meta:
        verbose_name = 'Данные для подключения Tinkoff'
        verbose_name_plural = 'Данные для подключения Tinkoff'

    terminal_key = models.CharField(
        verbose_name='Ключ терминала',
        help_text='Ключ терминала Tinkoff.',
        max_length=512,
        null=True,
        blank=True,
    )
    terminal_pass = models.CharField(
        verbose_name='Пароль терминала',
        help_text='Пароль терминала Tinkoff.',
        max_length=512,
        null=True,
        blank=True,
    )
    payment_success_url = models.URLField(
        verbose_name='Ссылка успешной оплаты',
        help_text=(
            'Ссылка на которую будет переведён пользователь после успешной оплаты заказа.'
        ),
        null=True,
        blank=True,
    )
    payment_fail_url = models.URLField(
        verbose_name='Ссылка неудачной оплаты',
        help_text=(
            'Ссылка на которую будет переведён пользователь после неудачной оплаты заказа.'
        ),
        null=True,
        blank=True,
    )

    def clean(self) -> None:
        return super().clean()


class EmailCredentials(AbstractBaseSoloModel):
    class Meta:
        verbose_name = 'Данные для подключения Email'
        verbose_name_plural = 'Данные для подключения Email'

    host = models.CharField(
        verbose_name='Представитель услуг (Host)',
        help_text='Host сервиса через который будет осуществятся отправка email',
        max_length=512,
        null=True,
        blank=True,
    )
    port = models.CharField(
        verbose_name='Порт SMTP',
        help_text='Порт SMTP сервера.',
        max_length=512,
        null=True,
        blank=True,
    )
    use_tls = models.BooleanField(
        verbose_name='Отправка по протоколу TLS',
        help_text=(
            'Если используется SSL - установить "Нет".'
        ),
        null=True,
        blank=True,
    )
    use_ssl = models.BooleanField(
        verbose_name='Отправка по протоколу SSL',
        help_text=(
            'Если используется TLS - установить "Нет".'
        ),
        null=True,
        blank=True,
    )
    host_user = models.CharField(
        verbose_name='Host e-mail',
        help_text='E-mail учётной записи, через который будет осуществятся отправка email.',
        max_length=512,
        null=True,
        blank=True,
    )
    host_password = models.CharField(
        verbose_name='Host password',
        help_text='Пароль для авторизации учётной записи.',
        max_length=512,
        null=True,
        blank=True,
    )
    default_from_email = models.EmailField(
        verbose_name='E-mail с которого будут отправляться письма',
        help_text='Обычно тот же, что и "Host e-mail".',
        null=True,
        blank=True,
    )

    def clean(self) -> None:
        if self.use_ssl and self.use_tls:
            raise exceptions.ValidationError(
                message=(
                    'TLS и SSL не могут быть использованы одновременно.'
                )
            )
        elif self.use_ssl and not self.use_tls:
            self.use_tls = False
        elif not self.use_ssl and self.use_tls:
            self.use_ssl = False

        if not self.use_ssl and not self.use_tls:
            use_ssl, use_tls = settings.EMAIL_USE_SSL, settings.EMAIL_USE_TLS
        else:
            use_ssl, use_tls = (True, False) if self.use_ssl else (False, True)
        try:
            connection = EmailBackend(
                host=self.host or settings.EMAIL_HOST,
                port=self.port or settings.EMAIL_PORT,
                use_tls=use_tls,
                use_ssl=use_ssl,
                host_user=self.host_user or settings.EMAIL_HOST_USER,
                host_password=self.host_password or settings.EMAIL_HOST_PASSWORD,
                default_from_email=self.default_from_email or settings.DEFAULT_FROM_EMAIL,
            )
            connection.open()
            connection.close()
        except Exception as error:
            if isinstance(error, SMTPAuthenticationError):
                logger.info(error)
                raise exceptions.ValidationError(
                    message=(
                        'Указан неверный логин или пароль.'
                    )
                )
            elif isinstance(error, TimeoutError):
                raise exceptions.ValidationError(
                    message=(
                        'От SMTP сервера нет ответа. Скорее всего неверно указан "Порт SMTP".'
                    )
                )
            elif isinstance(error, gaierror):
                raise exceptions.ValidationError(
                    message=(
                        'Неверно указаны "Представитель услуг (Host)" или "Порт SMTP" SMTP сервера.'
                    )
                )
            elif isinstance(error, SSLError):
                raise exceptions.ValidationError(
                    message=(
                        'Не допустимо использование SSL протокола.'
                    )
                )
            else:
                raise exceptions.ValidationError(
                    message=(
                        'Что-то пошло не так.'
                    )
                )
        return super().clean()

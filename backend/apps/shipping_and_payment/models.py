from django.core.validators import RegexValidator
from django.db import models

from apps.market.enum import PaymentMethod
from utils.abstractions.model import AbstractBaseModel, AbstractBaseSoloModel


class PaymentVariant(AbstractBaseModel):
    class Meta:
        verbose_name = "Вариант оплаты"
        verbose_name_plural = "Варианты оплаты"

    name = models.CharField(
        verbose_name="Название",
        help_text="Название варианта оплаты",
        max_length=512,
        unique=True,
        choices=PaymentMethod.choices,
    )

    def __str__(self) -> str:
        return dict(PaymentMethod.choices)[self.name]

    def __repr__(self) -> str:
        return self.__str__()


class Provider(AbstractBaseSoloModel):
    class Meta:
        verbose_name = 'Адрес поставщика'
        verbose_name_plural = 'Адрес поставщика'

    name = models.CharField(
        verbose_name='Название',
        help_text='Название',
        max_length=128,
        blank=True,
        null=True
    )
    phone_number = models.CharField(
        verbose_name='Номер телефона',
        help_text='Номер телефона',
        blank=True,
        null=True,
        validators=[RegexValidator(r'\A[+7,8]\d{11,12}')]
    )
    country = models.CharField(
        verbose_name='Страна',
        help_text='Страна',
        blank=True,
        null=True
    )
    city = models.CharField(
        verbose_name='Город',
        help_text='Город',
        blank=True,
        null=True
    )
    street = models.CharField(
        verbose_name='Улица',
        help_text='Улица',
        blank=True,
        null=True
    )
    house = models.CharField(
        verbose_name='Дом',
        help_text='Дом',
        blank=True,
        null=True
    )
    postal_code = models.CharField(
        verbose_name='Почтовый индекс',
        help_text='Почтовый индекс',
        blank=True,
        null=True
    )
    geo_lat = models.CharField(
        verbose_name='Широта',
        help_text='Широта',
        blank=True,
        null=True
    )
    geo_lon = models.CharField(
        verbose_name='Долгота',
        help_text='Долгота',
        blank=True,
        null=True
    )

    def str(self) -> str:
        return f'{self.country}, {self.city}, {self.house}'

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import Group
from django.contrib.auth.models import \
    PermissionsMixin as DefaultPermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.user.enum import GenderChoices, PaymentType
from utils.abstractions.model import AbstractBaseModel


class PermissionsMixin(DefaultPermissionsMixin):
    groups = models.ManyToManyField(
        Group,
        verbose_name='Группы',
        blank=True,
        help_text=(
            'Группы, к которым принадлежит этот пользователь. Пользователь получит'
            'все разрешения предоставляется каждой из их групп.'),
        related_name='users',
        related_query_name='user',
    )

    class Meta:
        abstract = True


class UserManager(BaseUserManager):
    """

    """

    def create_superuser(self, username: str, password: str) -> AbstractBaseUser:
        """

        """
        if not username:
            raise ValueError('Номер телефона пользователя не может быть пустым')

        user = self.model(username=username)
        user.set_password(password)
        user.is_superuser = True
        user.is_admin = True
        user.is_active = True
        user.first_name = 'GK'
        user.last_name = "Sport"
        user.second_name = 'admin'
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin, AbstractBaseModel):
    """
    Модель пользователя.
    """

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    password = models.CharField(_("password"), max_length=128, null=True, blank=True)
    is_admin = models.BooleanField(
        verbose_name='Пользователь может получить доступ к административной панели',
        help_text='Указывает, имеет ли пользователь статус администратора',
        default=False
    )
    is_active = models.BooleanField(
        verbose_name='Пользователь активен (не забанен)',
        help_text='Указывает, активирована ли учетная запись пользователя',
        default=True
    )
    username = models.CharField(
        verbose_name='Номер телефона',
        help_text='Номер телефона',
        max_length=13,
        validators=(
            RegexValidator(
                r'(\+7|7|8)?[\s\-]?\(?[375][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}'
            ),
        ),
        unique=True
    )
    update_username = models.CharField(
        verbose_name='Новый номер телефона',
        help_text='Номер телефона',
        max_length=12,
        validators=(
            RegexValidator(
                r'(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}'
            ),
        ),
        unique=True,
        blank=True,
        null=True
    )
    email = models.EmailField(
        verbose_name='E-mail пользователя',
        help_text='E-mail',
        blank=True,
        null=True,
    )
    first_name = models.CharField(
        verbose_name='Имя пользователя',
        help_text='Имя',
        max_length=80,
        blank=True,
        null=True,
    )
    second_name = models.CharField(
        verbose_name='Отчество пользователя',
        help_text='Отчество',
        max_length=80,
        blank=True,
        null=True,
    )
    last_name = models.CharField(
        help_text='Фамилия',
        verbose_name='Фамилия пользователя',
        max_length=80,
        blank=True,
        null=True,
    )
    birthdate = models.DateField(
        verbose_name='Дата рождения',
        help_text='Дата рождения пользователя',
        blank=True,
        null=True,
    )
    gender = models.CharField(
        verbose_name='Пол',
        help_text='Пол пользователя',
        max_length=6,
        choices=GenderChoices.choices,
        default=GenderChoices.MALE,
    )

    city = models.CharField(
        help_text='Город проживания пользователя',
        verbose_name='Город',
        max_length=256,
        blank=True,
        null=True,
    )
    street = models.CharField(
        help_text='Улица проживания пользователя',
        verbose_name='Улица',
        max_length=256,
        blank=True,
        null=True,
    )
    house_number = models.CharField(
        help_text='Номер дома пользователя',
        verbose_name='Дом',
        max_length=256,
        blank=True,
        null=True,
    )
    apartment_number = models.CharField(
        help_text='Номер квартиры | офиса пользователя',
        verbose_name='Квартира',
        max_length=256,
        blank=True,
        null=True,
    )

    last_login = models.DateTimeField(
        help_text='Указывает, когда пользователь входил в систему в последний раз',
        verbose_name='Время последнего входа в систему',
        auto_now=True
    )
    date_joined = models.DateTimeField(
        help_text='Указывает, когда пользователь был зарегистрирован',
        verbose_name='Дата регистрации пользователя',
        default=timezone.now
    )
    is_dealer = models.BooleanField(
        help_text='Является ли пользователь дилером',
        verbose_name='Является дилером',
        default=False
    )
    payment_method = models.CharField(
        help_text='Выбирается из списка возможных вариантов оплаты',
        verbose_name='Способ оплаты',
        choices=PaymentType.choices,
        default=PaymentType.PREPAID
    )
    agent_id = models.CharField(
        help_text='Идентификатор контрагента сервиса Мой Склад',
        verbose_name='Идентификатор контрагента сервиса Мой Склад',
        null=True,
        blank=True,
    )
    USERNAME_FIELD = 'username'
    objects = UserManager()

    @property
    def is_staff(self) -> bool:
        """
        Пользователь имеет доступ в админ-панель
        """
        return self.is_admin

    def clean(self) -> None:
        if not self.is_dealer and self.payment_method == PaymentType.POSTPAID:
            raise ValidationError('Постоплата доступна только дилерам')


class SMSKey(AbstractBaseModel):
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE,
        related_name='sms_key'
    )
    key = models.CharField(
        max_length=4
    )
    update_at = models.DateTimeField(
        verbose_name='Дата последнего обновления',
        auto_now_add=True,
        blank=True,
        null=True
    )

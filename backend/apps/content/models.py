from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models

from utils.abstractions.model import AbstractBaseModel, AbstractBaseSoloModel


class About(AbstractBaseSoloModel):
    class Meta:
        verbose_name = 'О нас'
        verbose_name_plural = verbose_name

    text1 = models.TextField(
        verbose_name='Текст 1',
        blank=True,
        null=True
    )
    image1 = models.ImageField(
        upload_to="content",
        verbose_name="Изображение для текст1",
        blank=True,
        null=True
    )
    text2 = models.TextField(
        verbose_name='Текст 2',
        blank=True,
        null=True
    )
    image2 = models.ImageField(
        upload_to="content",
        verbose_name="Изображение для текст2",
        blank=True,
        null=True
    )
    text3 = models.TextField(
        verbose_name='Текст 3',
        blank=True,
        null=True
    )
    image3 = models.ImageField(
        upload_to="content",
        verbose_name="Изображение для текст3",
        blank=True,
        null=True
    )

    def __str__(self) -> str:
        return "О компании"


class AboutImage(AbstractBaseModel):
    class Meta:
        verbose_name = 'Изображение для страницы "О компании"'
        verbose_name_plural = 'Изображения для страницы "О компании"'

    image = models.ImageField(upload_to='images', verbose_name='Изображение')
    about = models.ForeignKey(to=About,
                              null=True,
                              verbose_name='Страница "О компании"',
                              related_name='images',
                              on_delete=models.SET_NULL)

    def __str__(self) -> str:
        return self.image.url


class Banner(AbstractBaseModel):
    class Meta:
        ordering = ('priority',)
        verbose_name = 'Баннер'
        verbose_name_plural = 'Баннеры'

    name = models.CharField(verbose_name='Название баннера', max_length=1023, default='', unique=True)
    banner_image = models.ImageField(upload_to='content', verbose_name='Изображение баннера')
    adaptive_image = models.ImageField(upload_to='content', verbose_name='Изображение баннера для мобильных устройств')
    is_active = models.BooleanField(verbose_name='Активно', default=False)
    priority = models.PositiveSmallIntegerField(verbose_name='Порядковый номер баннера', blank=True, null=True)
    banner_link = models.URLField(verbose_name='Ссылка баннера', blank=True, null=True)

    def __str__(self) -> str:
        return f'banner {self.banner_image}'


class FAQ(AbstractBaseModel):
    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQ'
        ordering = ('priority',)

    question = models.TextField(verbose_name='Вопрос')
    answer = models.TextField(verbose_name='Ответ')
    priority = models.PositiveSmallIntegerField(verbose_name='Приоритет', blank=True, null=True)

    def __str__(self) -> str:
        return self.question


class Header(AbstractBaseSoloModel):
    singleton_instance_id = 1

    class Meta:
        verbose_name = 'Хэдер'
        verbose_name_plural = verbose_name

    logo = models.ImageField(upload_to='logo', verbose_name='Логотип', blank=True)

    def __str__(self) -> str:
        return 'Header'


class Contact(AbstractBaseSoloModel):
    singleton_instance_id = 1

    class Meta:
        verbose_name = 'Контакты'
        verbose_name_plural = verbose_name

    phone_number = models.CharField(
        verbose_name='Номер телефона',
        help_text='Основной',
        max_length=12,
        blank=True,
        validators=[RegexValidator(r'\A[+7,8]\d{11,12}')]
    )
    email = models.EmailField(
        verbose_name='email',
        null=True,
        blank=True
    )
    whatsapp1 = models.CharField(
        verbose_name='Номер whatsapp1',
        help_text='Номер whatsapp1',
        max_length=12,
        null=True,
        blank=True,
        validators=[RegexValidator(r'\A[+7,8]\d{11,12}')]
    )
    whatsapp2 = models.CharField(
        verbose_name='Номер whatsapp2',
        help_text='Номер whatsapp2',
        max_length=12,
        null=True,
        blank=True,
        validators=[RegexValidator(r'\A[+7,8]\d{11,12}')]
    )
    telegram = models.CharField(
        verbose_name='Телеграмм',
        help_text='Телеграмм',
        max_length=12,
        null=True,
        blank=True,
    )
    vk = models.CharField(
        verbose_name='В контакте',
        help_text='В контакте',
        max_length=128,
        null=True,
        blank=True,
    )
    ok = models.CharField(
        verbose_name='Одноклассники',
        help_text='Одноклассники',
        max_length=128,
        null=True,
        blank=True,
    )
    youtube = models.URLField(
        verbose_name='Youtube',
        help_text='youtube',
        max_length=64,
        blank=True,
        null=True
    )
    address = models.CharField(
        verbose_name='Адрес',
        help_text='Адрес',
        max_length=255,
        null=True,
        blank=True,
    )
    latitude = models.CharField(
        verbose_name='Широта',
        help_text='Широта',
        max_length=16,
        null=True,
        blank=True,
    )
    longitude = models.CharField(
        verbose_name='Долгота',
        help_text='Долгота',
        max_length=16,
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return f'{self.phone_number}'


class RecipientEmail(models.Model):
    email = models.EmailField(verbose_name='email')
    contacts = models.ForeignKey(
        to=Contact,
        on_delete=models.CASCADE,
        related_name='recipient_emails',
        verbose_name='Контакты',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Email для отправки'
        verbose_name_plural = 'Email`ы для отправки'

    def __str__(self) -> str:
        return f'{self.email}'

    def __repr__(self) -> str:
        return self.__str__()


class Documents(AbstractBaseSoloModel):
    class Meta:
        verbose_name = 'Документы'
        verbose_name_plural = 'Документы'

    user_agreement = models.FileField(
        upload_to='documents',
        verbose_name='Политика оферты',
        help_text='Файл PDF с политикой оферты',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                ['pdf'], message='Для загрузки доступны только PDF файлы'
            )
        ]
    )
    privacy_policy = models.FileField(
        upload_to='documents',
        verbose_name='Политика конфиденциальности',
        help_text='Файл политики конфиденциальности',
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                ['pdf'], message='Для загрузки доступны только PDF файлы'
            )
        ]
    )

    def __str__(self) -> str:
        return 'Документы'


class DeliveryMethod(AbstractBaseModel):
    class Meta:
        verbose_name = 'Способ доставки'
        verbose_name_plural = 'Способы доставки'

    name = models.CharField(
        verbose_name='Название',
        help_text='Название',
        max_length=128,
        blank=True,
        null=True
    )
    description = models.TextField(
        verbose_name='Описание способа доставки',
        blank=True,
        null=True
    )
    priority = models.PositiveSmallIntegerField(
        verbose_name='Приоритет',
        help_text='Приоритет',
        default=0,
    )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name


class ReturnConditions(AbstractBaseSoloModel):
    class Meta:
        verbose_name = 'Условия возврата'
        verbose_name_plural = verbose_name

    text = models.TextField(
        verbose_name='Текст для страницы "Условия возврата"',
        blank=True,
        null=True,
    )

    def __str__(self) -> str:
        if self.text:
            return self.text[:30]
        return ''

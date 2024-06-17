import uuid

from colorfield.fields import ColorField
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import (Case, DecimalField, F, Index, Min, Q, QuerySet,
                              Sum, When)
from mptt.models import TreeForeignKey

from apps.market.enum import (BasketStatus, ColorSample, PaymentMethod,
                              PaymentStatus, TypeLabel)
from apps.market.validators import validate_nonzero
from apps.user.models import User
from utils.abstractions.model import AbstractBaseModel, AbstractionMPTTModel
from utils.fields import ImageOrSVGField


class Category(AbstractionMPTTModel):
    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = 'Категория товара'
        verbose_name_plural = 'Категории товара'

    is_active = models.BooleanField(
        verbose_name='Активно',
        help_text='Активно',
        default=False
    )
    name = models.CharField(
        max_length=50,
        unique=False,
        verbose_name='Название категории'
    )
    category_image = models.ImageField(upload_to='market',
                                       verbose_name='Изображение категории',
                                       blank=True,
                                       null=True)
    parent = TreeForeignKey(to='self',
                            on_delete=models.PROTECT,
                            verbose_name='Родительская категория',
                            null=True,
                            blank=True,
                            related_name='children')

    def clean(self) -> None:
        if self.parent and (not self.parent.is_active and self.is_active):
            raise ValidationError('Нельзя активировать категорию, если не активна родительская категория')
        if Category.objects.filter(id=self.id).exists():
            children_category = self.get_descendants()
            if not self.is_active:
                children_category.update(is_active=False)

    def get_full_name(self) -> str:
        if self.parent:
            return f'{self.parent.get_full_name()} > {self.name}'
        return self.name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class Label(AbstractBaseModel):
    class Meta:
        verbose_name = 'Лейбл'
        verbose_name_plural = 'Лейблы'
        ordering = ('priority',)

    priority = models.PositiveSmallIntegerField(verbose_name='Приоритет',
                                                unique=True,
                                                null=True,
                                                validators=[validate_nonzero])
    name = models.CharField(verbose_name='Имя лейбла', unique=True)
    type_label = models.CharField(verbose_name='Тип лейбла', choices=TypeLabel.choices, default=TypeLabel.CUSTOM)
    color = ColorField(samples=ColorSample.choices, null=True, blank=True, verbose_name='Цвет')

    def name_and_type_mapping(
            self,
            *,
            type_label: str,
            name_label: str
    ) -> None:
        if self.type_label == type_label and self.name != name_label:
            raise ValidationError('Имя этого лейбла нельзя менять')

    def clean(self) -> None:
        self.name_and_type_mapping(type_label=TypeLabel.PROMOTION.value, name_label=TypeLabel.PROMOTION.label)
        self.name_and_type_mapping(type_label=TypeLabel.NEW.value, name_label=TypeLabel.NEW.label)
        self.name_and_type_mapping(type_label=TypeLabel.BESTSELLER.value, name_label=TypeLabel.BESTSELLER.label)
        if self.type_label == TypeLabel.PROMOTION.value and self.priority != 1:
            raise ValidationError('Приоритет этого лейбла нельзя менять. Обновите страницу.')

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class Brand(AbstractBaseModel):
    class Meta:
        verbose_name = 'Бренд'
        verbose_name_plural = 'Бренды'
        ordering = ('priority',)

    id = models.CharField(
        verbose_name='Идентификатор',
        help_text='Идентификатор Moi Sklad.',
        max_length=512,
        unique=True,
        primary_key=True
    )
    name = models.CharField(
        verbose_name='Название',
        help_text='Название товара отображаемое на сайте и используемое при поиске.',
        max_length=512,
        null=True,
        blank=True,
    )
    priority = models.PositiveSmallIntegerField(
        verbose_name='Приоритет',
        help_text='Порядковый номер',
        blank=True,
        null=True
    )
    image = models.ImageField(upload_to='market/brands',
                              verbose_name='Изображение',
                              blank=True,
                              null=True)
    page_title = models.CharField(
        verbose_name='Заголовок страницы',
        help_text='Заголовок в табе страницы',
        max_length=256,
        blank=True,
        null=True
    )
    meta_description = models.TextField(
        verbose_name='meta_description',
        help_text='Описание страницы',
        blank=True,
        null=True,
    )
    h1 = models.TextField(
        verbose_name='h1',
        help_text='Заголовок h1',
        blank=True,
        null=True,
    )
    text_under_title = models.TextField(
        verbose_name='Текст под заголовком',
        help_text='Текст под заголовком',
        blank=True,
        null=True
    )
    text_under_product = models.TextField(
        verbose_name='Текст под товарами',
        help_text='Текст под товарами',
        blank=True,
        null=True
    )
    breadcrumb = models.CharField(
        verbose_name='Breadcrumb',
        help_text='Breadcrumb',
        max_length=100,
        blank=True,
        null=True,
    )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class ProductManager(models.Manager):

    def get_prepared_products(self) -> QuerySet:
        qs = self.model.objects.get_queryset()
        queryset = (
            qs.annotate(
                price_variants=Sum("variants__price"),
            )
            .filter(Q(Q(variants__is_active=True) & Q(variants__archived=False)))
            .exclude(
                Q(is_active=False)
                | Q(category__isnull=True)
                | Q(price_variants=0)
                | Q(variants__isnull=True)
                | Q(weight=0)
                | Q(archived=True)
            )
            .order_by("-updated_at")
        )
        return queryset

    def get_products_on_display(self) -> QuerySet:
        qs = self.model.objects.get_prepared_products()
        queryset = qs.annotate(
            min_variant_price=Min("variants__price", filter=Q(variants__price__gt=0)),
            price_with_discount=Min('variants__sale_price'),
            price_for_filter=Case(
                When(price_with_discount=0, then='min_variant_price'),
                default=Min('variants__sale_price', filter=Q(variants__sale_price__gt=0))
            )
        ).filter(Q(variants__quantity__gt=0) | Q(variants__to_order=True))
        return queryset


class Product(AbstractBaseModel):
    class Meta:
        verbose_name = 'Товар на витрине'
        verbose_name_plural = 'Товары на витрине'

    archived = models.BooleanField(
        verbose_name='Архивированный товар',
        help_text='Статус архивированности товара.',
        default=False,
    )
    id = models.CharField(
        verbose_name='Идентификатор',
        help_text='Идентификатор Moi Sklad.',
        max_length=512,
        unique=True,
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
    )
    name = models.CharField(
        verbose_name='Название',
        help_text='Название товара отображаемое на сайте и используемое при поиске.',
        max_length=512,
        db_index=True,
        null=True,
        blank=True,
    )
    code = models.CharField(
        verbose_name='Код товара',
        help_text='Код товара Moi Sklad.',
        max_length=512,
        null=True,
        blank=True,
    )
    description = models.TextField(
        verbose_name='Описание товара',
        help_text='Описание товара Moi Sklad.',
        null=True,
        blank=True,
    )
    external_code = models.CharField(
        verbose_name='Дополнительный код товара',
        help_text='Дополнительный код товара Moi Sklad.',
        max_length=512,
        null=True,
        blank=True,
    )
    article = models.CharField(
        verbose_name='Артикул',
        help_text='Артикул товара.',
        max_length=512,
        null=True,
        blank=True,
    )
    weight = models.DecimalField(
        verbose_name='Вес',
        help_text='Вес товара в кг.',
        decimal_places=2,
        max_digits=20,
        null=True,
        blank=True,
    )
    volume = models.DecimalField(
        verbose_name='Объем',
        help_text='Объем товара.',
        decimal_places=2,
        max_digits=20,
        null=True,
        blank=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Время обновления',
    )
    is_active = models.BooleanField(
        verbose_name='Активность',
        help_text='Активность товара',
        default=True,
    )
    brand = models.ForeignKey(
        to=Brand,
        verbose_name='Бренд',
        related_name='products',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    category = models.ManyToManyField(
        to=Category,
        verbose_name='Категория',
        related_name='products',
        blank=True
    )
    label = models.ForeignKey(to=Label,
                              verbose_name='Лейбл',
                              blank=True,
                              null=True,
                              on_delete=models.SET_NULL,
                              related_name='products'
                              )
    crossale = models.ManyToManyField(to='self',
                                      verbose_name='Рекомендуемые товары',
                                      blank=True,
                                      through='CrossSaleProduct',
                                      symmetrical=False)
    user = models.ManyToManyField(to=User,
                                  verbose_name='Избранное пользователя',
                                  blank=True,
                                  related_name='products',
                                  through='Favorite',
                                  through_fields=('product', 'user'),
                                  symmetrical=False)
    objects = ProductManager()

    def clean(self) -> None:
        has_sale_price = self.variants.filter(sale_price__gt=0).exists()
        if self.label:
            if has_sale_price:
                self.label = Label.objects.filter(type_label=TypeLabel.PROMOTION).first()
            elif self.label.type_label == TypeLabel.PROMOTION:
                raise ValidationError('Товару без цены распродажи нельзя назначить лейбл "Скидка"')
        else:
            if has_sale_price:
                raise ValidationError('Товару с указанной ценой распродажи должен быть назначен лейбл "Скидка"')

    def __str__(self) -> str:
        return f'Название: {self.name}, артикул: {self.article}'

    def __repr__(self) -> str:
        return self.__str__()


class Favorite(AbstractBaseModel):
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    product = models.ForeignKey(to=Product,
                                verbose_name='Товар в избранном',
                                blank=True,
                                null=True,
                                on_delete=models.CASCADE)
    user = models.ForeignKey(to=User,
                             verbose_name='Пользователь у которого товар в избранном',
                             blank=True,
                             null=True,
                             on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.user.username} <3 {self.product.name}"

    def __repr__(self) -> str:
        return self.__str__()


class ShowcaseProduct(Product):
    class Meta:
        verbose_name = 'Поступление со склада'
        verbose_name_plural = 'Поступления со склада'
        proxy = True


class CrossSaleProduct(AbstractBaseModel):
    class Meta:
        verbose_name = 'Рекомендация'
        verbose_name_plural = 'Рекомендации'
        unique_together = ('product', 'recommendet')

    product = models.ForeignKey(to=Product,
                                verbose_name='Основной товар',
                                related_name='recommendet',
                                on_delete=models.CASCADE)
    recommendet = models.ForeignKey(to=Product,
                                    verbose_name='Рекомендуемый товар',
                                    related_name='products',
                                    on_delete=models.CASCADE)


class ProductImage(AbstractBaseModel):
    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товара'

    id = models.CharField(
        verbose_name='Идентификатор',
        help_text='Идентификатор Moi Sklad.',
        max_length=512,
        unique=True,
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
    )
    image = ImageOrSVGField(
        upload_to='market/products',
        verbose_name='Изображение',
    )
    miniature = ImageOrSVGField(
        upload_to='market/products',
        verbose_name='Миниатюра',
        null=True
    )
    priority = models.PositiveSmallIntegerField(
        verbose_name='Приоритет',
        help_text='Порядковый номер отображения на сайте',
        default=32767,
        null=True
    )
    product = models.ForeignKey(
        to=Product,
        verbose_name='Товар',
        related_name='images',
        on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return self.product.name + " Картинка " + str(self.priority)

    def __repr__(self) -> str:
        return self.__str__()


class VariantManager(models.Manager):

    def get_variant_discount(self) -> QuerySet:
        qs = self.get_queryset().annotate(
            variant_discount=Case(
                When(sale_price__gt=0, then=F('price') - F('sale_price')),
                default=0,
                output_field=models.DecimalField()
            )
        )
        return qs


class Variant(AbstractBaseModel):
    class Meta:
        verbose_name = 'Вариант'
        verbose_name_plural = 'Варианты'

    id = models.CharField(
        verbose_name='Идентификатор',
        help_text='Идентификатор Moi Sklad.',
        max_length=512,
        unique=True,
        primary_key=True,
        editable=False,
    )
    archived = models.BooleanField(
        verbose_name='Архивированный вариант',
        help_text='Статус активности варианта.',
        default=True,
        null=False,
        blank=True,
    )
    to_order = models.BooleanField(
        verbose_name='Вариант под заказ',
        help_text='Вариант товара будет под заказ.',
        default=False,
        null=True,
        blank=True,
    )
    name = models.CharField(
        verbose_name='Название',
        help_text='Название варианта отображаемое на сайте и используемое при поиске.',
        max_length=512,
        null=True,
        blank=True,
    )
    code = models.CharField(
        verbose_name='Код варианта',
        help_text='Код варианта Moi Sklad.',
        max_length=512,
        null=True,
        blank=True,
    )
    external_code = models.CharField(
        verbose_name='Дополнительный код варианта',
        help_text='Дополнительный код варианта Moi Sklad.',
        max_length=512,
        null=True,
        blank=True,
    )
    price = models.DecimalField(
        verbose_name='Цена',
        help_text='Цена варианта.',
        decimal_places=2,
        max_digits=20,
        null=True,
        blank=True,
    )
    stock = models.DecimalField(
        verbose_name='Остаток',
        help_text='Остаток варианта.',
        decimal_places=2,
        max_digits=20,
        null=True,
        blank=True,
    )
    reserve = models.DecimalField(
        verbose_name='Резерв',
        help_text='Варианты в резерве.',
        decimal_places=2,
        max_digits=20,
        null=True,
        blank=True,
    )
    quantity = models.DecimalField(
        verbose_name='Доступно',
        help_text='Количество варианта.',
        decimal_places=2,
        max_digits=20,
        null=True,
        blank=True,
    )
    sale_price = models.DecimalField(
        verbose_name='Цена распродажи',
        help_text='Цена распродажи варианта.',
        decimal_places=2,
        max_digits=20,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(
        verbose_name='Активность',
        help_text='Активность варианта',
        default=True,
        blank=True,
        null=True
    )
    product = models.ForeignKey(
        to=Product,
        verbose_name='Товар',
        related_name='variants',
        on_delete=models.CASCADE
    )

    objects = VariantManager()

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class VariantImage(AbstractBaseModel):
    class Meta:
        verbose_name = 'Изображение варианта'
        verbose_name_plural = 'Изображения варианта'
        unique_together = ['image', 'variant']

    image = ImageOrSVGField(
        upload_to='market/variants',
        verbose_name='Изображение',
    )
    variant = models.ForeignKey(
        to=Variant,
        verbose_name='Вариант',
        related_name='images',
        on_delete=models.CASCADE
    )


class Characteristic(AbstractBaseModel):
    class Meta:
        verbose_name = 'Вид характеристики'
        verbose_name_plural = 'Виды характеристик'

    id = models.CharField(
        verbose_name='Идентификатор',
        help_text='Идентификатор Moi Sklad.',
        max_length=512,
        unique=True,
        primary_key=True
    )
    name = models.CharField(
        verbose_name='Название',
        help_text='Название характеристики.',
        max_length=512,
        null=True,
        blank=True,
    )


class VariantCharacteristics(AbstractBaseModel):
    class Meta:
        verbose_name = 'Характеристика'
        verbose_name_plural = 'Характеристики'
        unique_together = ['type', 'variant']

    type = models.ForeignKey(
        to=Characteristic,
        verbose_name='Вид характеристики',
        related_name='variant_characteristics',
        on_delete=models.CASCADE,
        null=True
    )
    value = models.CharField(
        verbose_name='Значение',
        help_text='Значение характеристики.',
        max_length=512,
        null=True,
        blank=True,
    )
    variant = models.ForeignKey(
        to=Variant,
        verbose_name='Вариант',
        related_name='characteristics',
        on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return self.type.name

    def __repr__(self) -> str:
        return self.__str__()


class ProductCharacteristics(AbstractBaseModel):
    class Meta:
        verbose_name = 'Характеристика'
        verbose_name_plural = 'Характеристики'
        unique_together = ['type', 'product']
        indexes = (Index(fields=('value',)),)

    type = models.ForeignKey(
        to=Characteristic,
        verbose_name='Вид характеристики',
        related_name='product_characteristics',
        on_delete=models.CASCADE,
        null=True
    )
    value = models.TextField(
        verbose_name='Значение',
        help_text='Значение характеристики.',
        null=True,
        blank=True,
    )
    product = models.ForeignKey(
        to=Product,
        verbose_name='Вариант',
        related_name='characteristics',
        on_delete=models.CASCADE,
        db_index=True
    )

    def __str__(self) -> str:
        return self.type.name

    def __repr__(self) -> str:
        return self.__str__()


class Tag(AbstractBaseModel):
    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    name = models.CharField(verbose_name='Название тега', max_length=127, unique=True)
    priority = models.PositiveSmallIntegerField(verbose_name='Приоритет', default=32767, null=True)
    page_title = models.CharField(
        verbose_name='Заголовок страницы',
        help_text='Заголовок в табе страницы',
        max_length=256,
        blank=True,
        null=True
    )
    product = models.ManyToManyField(to=Product,
                                     verbose_name='Товары',
                                     blank=True,
                                     through='TagProduct',
                                     related_name='tags',
                                     through_fields=('tag', 'product'),
                                     symmetrical=False,
                                     )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class TagProduct(AbstractBaseModel):
    class Meta:
        verbose_name = 'Связь "тег - товар"'

    tag = models.ForeignKey(
        to=Tag,
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        to=Product,
        on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return f'Связь Тег: {self.tag.name} - товар: {self.product.name}'


class OrderState(AbstractBaseModel):
    class Meta:
        verbose_name = 'Статус заказа'
        verbose_name_plural = 'Статусы заказов'

    name = models.CharField(verbose_name='Название статуса', max_length=100)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class Basket(AbstractBaseModel):
    class Meta:
        verbose_name = 'Заказы'
        verbose_name_plural = 'Заказы'

    status = models.CharField(
        verbose_name='Статус корзины клиента',
        choices=BasketStatus.choices,
        default=BasketStatus.IS_ACTIVE
    )
    update_at = models.DateTimeField(
        verbose_name='Дата и время последнего обновления',
        help_text='Дата и время последнего обновления',
        auto_now=True,
        null=True,
        blank=True
    )
    total_cost = models.DecimalField(
        verbose_name='Общая стоимость',
        help_text='Общая стоимость корзины',
        decimal_places=2,
        max_digits=20,
        null=True,
        blank=True,
    )
    discount = models.DecimalField(
        verbose_name='Итоговая скидка',
        help_text='Итоговая скидка на товары в корзине',
        decimal_places=2,
        max_digits=20,
        null=True,
        blank=True,
    )
    order_number = models.CharField(
        max_length=50,
        verbose_name='Номер заказа',
        null=True,
        blank=True
    )
    order_paymentin = models.CharField(
        max_length=50,
        verbose_name='Номер выплаты заказа',
        null=True,
        blank=True
    )
    address = models.CharField(
        max_length=500,
        verbose_name='Полный адрес',
        null=True,
        blank=True
    )
    customer_phone = models.CharField(
        max_length=20,
        verbose_name='Номер телефона получателя',
        null=True,
        blank=True,
        validators=[
            RegexValidator(r'\A[+,8]\d{10,13}', 'Телефон должен содержать от 11 до 13 цифр.')
        ]
    )
    customer_name = models.CharField(
        max_length=100,
        verbose_name='Имя получателя',
        blank=True,
        null=True
    )
    customer_surname = models.CharField(
        max_length=100,
        verbose_name='Фамилия получателя',
        blank=True,
        null=True
    )
    customer_email = models.EmailField(
        verbose_name='E-mail получателя',
        blank=True,
        null=True
    )
    order_state = models.ForeignKey(
        to=OrderState,
        verbose_name='Статус заказа',
        related_name='orders',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    delivery_price = models.DecimalField(
        verbose_name='Стоимость доставки',
        help_text='Стоимость доставки',
        decimal_places=2,
        max_digits=20,
        null=True,
        blank=True,
        default=0.00
    )
    delivery_period = models.PositiveSmallIntegerField(
        verbose_name='Срок доставки',
        help_text='Срок доставки товара',
        default=0,
        null=True,
        blank=True
    )
    delivery_date_from = models.DateField(
        verbose_name='Дата доставки',
        help_text='Минимальная дата доставки',
        blank=True,
        null=True
    )
    delivery_date_to = models.DateField(
        verbose_name='Дата доставки',
        help_text='Максимальная дата доставки',
        blank=True,
        null=True
    )
    delivery_time = models.PositiveSmallIntegerField(
        verbose_name='Время доставки',
        help_text='Время доставки',
        blank=True,
        null=True
    )
    pvz_code = models.CharField(
        verbose_name='Пункт выдачи заказа',
        help_text='Код пункта выдачи заказа СДЭК',
        null=True,
        blank=True
    )
    payment_method = models.CharField(
        verbose_name='Способ платежа',
        choices=PaymentMethod.choices,
        blank=True,
        null=True
    )
    payment_url = models.URLField(
        verbose_name='Ссылка на оплату',
        blank=True,
        null=True
    )
    payment_status = models.CharField(
        verbose_name='Статус оплаты',
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID
    )
    order_date = models.DateTimeField(
        verbose_name='Дата совершения заказа',
        null=True,
        blank=True
    )
    token = models.UUIDField(verbose_name='Токен платежа',
                             null=True,
                             blank=True
                             )  # null_by_design
    payment_id = models.CharField(
        verbose_name='Идентификатор платежа',
        max_length=64,
        unique=True,
        null=True,
        blank=True
    )  # null_by_capability
    postal_code = models.CharField(
        verbose_name='Индекс',
        help_text='Почтовый индекс',
        null=True,
        blank=True
    )
    country = models.CharField(
        verbose_name='Страна получателя',
        help_text='Страна получателя',
        null=True,
        blank=True
    )
    city = models.CharField(
        verbose_name='Город получателя',
        help_text='Город получателя',
        null=True,
        blank=True
    )
    region = models.CharField(
        verbose_name='Регион',
        help_text='Регион',
        null=True,
        blank=True
    )
    street_with_type = models.CharField(
        verbose_name='Улица',
        help_text='Улица',
        null=True,
        blank=True
    )
    house_type_full = models.CharField(
        verbose_name='Тип строения',
        help_text='Тип строения (дом, корпус и т. д.)',
        null=True,
        blank=True
    )
    house = models.CharField(
        verbose_name='Индекс',
        help_text='Почтовый индекс',
        null=True,
        blank=True
    )
    block_type_full = models.CharField(
        verbose_name='Тип блока',
        help_text='Тип блока',
        null=True,
        blank=True
    )
    block = models.CharField(
        verbose_name='Блок',
        help_text='Блок',
        null=True,
        blank=True
    )
    flat = models.CharField(
        verbose_name='Квартира',
        help_text='Квартира',
        null=True,
        blank=True
    )
    unparsed_parts = models.CharField(
        verbose_name='Комментарий',
        help_text='Комментарий',
        null=True,
        blank=True
    )
    geo_lat = models.CharField(
        verbose_name='Широта',
        help_text='Координаты. Широта',
        null=True,
        blank=True
    )
    geo_lon = models.CharField(
        verbose_name='Долгота',
        help_text='Координаты. Долгота',
        null=True,
        blank=True
    )
    country_iso_code = models.CharField(
        verbose_name='Код страны',
        help_text='Код страны',
        null=True,
        blank=True
    )
    city_fias_id = models.CharField(
        verbose_name='ФИАС города',
        help_text='ФИАС города',
        null=True,
        blank=True
    )
    city_kladr_id = models.CharField(
        verbose_name='КЛАДР',
        help_text='КЛАДР',
        null=True,
        blank=True
    )
    buy_to_order = models.BooleanField(
        verbose_name='Покупка под заказ',
        help_text='Покупка под заказ',
        default=False,
        blank=True,
        null=True
    )
    user = models.ForeignKey(
        to=User,
        verbose_name='Клиент',
        related_name='baskets',
        on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return f'Корзина пользователя {self.user.username}'


class ActiveBasket(Basket):
    class Meta:
        verbose_name = 'Корзина активная'
        verbose_name_plural = 'Корзины активные'
        proxy = True


class ItemBasketManager(models.Manager):

    def get_cost_info(self) -> QuerySet:
        """
        Возвращает кверисет с добавленными полями without_discount, with_discount, item_discount,
        в которых отображается цена элемента корзины со скидкой и без скидки умноженные на
        значение поля quantity, а так же итоговую скидку на элемент корзины с учётом его количества
        """
        queryset = self.get_queryset().annotate(
            without_discount=F('price') * F('quantity'),
            with_discount=F('without_discount') - F('item_discount'),
            item_total_discount=(
                Case(
                    When(
                        sale_price__gt=0,
                        then=(F('price') - F('sale_price')) * F('quantity')
                    ),
                    When(
                        sale_price__isnull=True,
                        then=0
                    ),
                    When(
                        sale_price=0,
                        then=0
                    ),
                    default=0,
                    output_field=DecimalField()
                )
            )
        )
        return queryset

    def get_settlement_cost_info(self) -> QuerySet:
        """
        Расчётная цена корзины до момента подтверждения заказа.
        """
        queryset = self.get_queryset().annotate(
            enough_quantity=(
                Case(
                    When(
                        Q(quantity__lte=F('variant_product__stock'))
                        | Q(variant_product__to_order=True),
                        then=F('quantity')
                    ),
                    default=F('variant_product__stock'),
                    output_field=DecimalField()
                )
            ),
            settlement_total_price=F('variant_product__price') * F('enough_quantity'),
            settlement_discount=(
                Case(
                    When(
                        variant_product__sale_price__gt=0,
                        then=(F('variant_product__price') - F('variant_product__sale_price')) * F('enough_quantity')
                    ),
                    When(
                        variant_product__sale_price__isnull=True,
                        then=0
                    ),
                    default=0,
                    output_field=DecimalField()
                )
            )
        )
        return queryset


class ItemBasket(AbstractBaseModel):
    class Meta:
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзине'
        ordering = ('id',)

    code = models.CharField(
        verbose_name='Код варианта товара',
        max_length=512,
        null=True,
        blank=True
    )
    name = models.CharField(
        verbose_name='Название',
        help_text='Название товара добавленного в корзину',
        max_length=512,
        null=True,
        blank=True,
    )
    article = models.CharField(
        verbose_name='Артикул',
        help_text='Артикул товара',
        max_length=128,
        null=True,
        blank=True
    )
    price = models.DecimalField(
        verbose_name='Цена',
        help_text='Цена добавленного в корзину.',
        decimal_places=2,
        max_digits=20,
        null=True,
        blank=True,
    )
    sale_price = models.DecimalField(
        verbose_name='Цена распродажи',
        help_text='Цена распродажи товара добавленного в корзину',
        decimal_places=2,
        max_digits=20,
        null=True,
        blank=True,
    )
    quantity = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        help_text='Количество товара в корзине',
        default=1,
        validators=[MinValueValidator(1)]
    )
    item_total_cost = models.DecimalField(
        verbose_name='Общая стоимость товара',
        help_text='Стоимость указанного количества одного наименования товара',
        decimal_places=2,
        max_digits=20,
        null=True,
        blank=True,
    )
    item_total_cost_with_discount = models.DecimalField(
        verbose_name='Общая стоимость товара со скидкой',
        help_text='Стоимость указанного количества одного наименования товара со скидкой',
        decimal_places=2,
        max_digits=20,
        null=True,
        blank=True,
    )
    item_discount = models.DecimalField(
        verbose_name='Общая скидка товара',
        help_text='Общая скидка на наименование в корзине',
        decimal_places=2,
        max_digits=20,
        null=True,
        blank=True,
    )
    variant_product = models.ForeignKey(
        to=Variant,
        verbose_name='Вариант товара',
        related_name='item_baskets',
        on_delete=models.DO_NOTHING,
        null=True,
    )
    basket = models.ForeignKey(
        to=Basket,
        verbose_name='Корзина',
        related_name='item_baskets',
        on_delete=models.CASCADE,
    )
    objects = ItemBasketManager()

    def __str__(self) -> str:
        if self.name:
            return f'{self.name}'
        return self.variant_product.name


class ItemActiveBasket(ItemBasket):
    class Meta:
        verbose_name = 'Товар в активной корзине'
        verbose_name_plural = 'Товары в активной корзине'
        proxy = True

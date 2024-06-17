import calendar
import decimal
import json
from decimal import Decimal

from django.contrib import admin, messages
from django.contrib.admin import ModelAdmin, StackedInline
from django.core.files.base import ContentFile
from django.core.handlers.wsgi import WSGIRequest
from django.core.mail import send_mail
from django.db.models import Case, F, Q, QuerySet, Sum, When
from django.db.models.functions import TruncMonth
from django.forms import BaseModelFormSet
from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.shortcuts import render
from django.utils.html import format_html
from django.utils.safestring import SafeString, mark_safe
from django.utils.translation import gettext as _
from lxml.etree import tostring
from mptt.admin import DraggableMPTTAdmin
from mptt.querysets import TreeQuerySet

from apps.market.admin.forms import (BrandAdminForm, CategoryAdminForm,
                                     SetCategoryForm)
from apps.market.enum import BasketStatus
from apps.market.models import (ActiveBasket, Basket, Brand, Category,
                                ItemBasket, Label, Product, ProductImage,
                                ShowcaseProduct, Tag, Variant)
from utils.abstractions.admin import AbstractSoloAdmin, ReadOnlyStackedInline


@admin.action(description="Товар под заказ")
def make_to_order(
        modeladmin: ModelAdmin, request: WSGIRequest, queryset: QuerySet
) -> None:
    variants_queryset = Variant.objects.filter(
        product_id__in=queryset.values_list("id", flat=True)
    )
    variants_queryset.update(to_order=True)
    products = Product.objects.filter(id__in=variants_queryset)
    products.update(is_active=True)


class NoVariantFilter(admin.SimpleListFilter):
    title = "Товары без вариантов"
    parameter_name = "no variant"

    def lookups(self, request: WSGIRequest, model_admin: ModelAdmin) -> tuple:
        return (
            ("yes", "Yes"),
            ("no", "No"),
        )

    def queryset(self, request: WSGIRequest, queryset: QuerySet) -> QuerySet:
        if self.value() == "yes":
            return queryset.exclude(variants__isnull=False)
        elif self.value() == "no":
            return queryset.exclude(variants__isnull=True)


class ImageFilter(admin.SimpleListFilter):
    title = "Наличие картинки"
    parameter_name = "have_image"

    def lookups(self, request: WSGIRequest, model_admin: ModelAdmin) -> tuple:
        return (
            ("yes", "Есть хотя бы одна"),
            ("no", "Нет"),
        )

    def queryset(self, request: WSGIRequest, queryset: QuerySet) -> QuerySet:
        if self.value() == "yes":
            return queryset.exclude(images__isnull=True)
        elif self.value() == "no":
            return queryset.exclude(images__isnull=False)


class DiscountFilter(admin.SimpleListFilter):
    title = "Акционные товары"
    parameter_name = "under_discount"

    def lookups(self, request: WSGIRequest, model_admin: ModelAdmin) -> tuple:
        return (
            ("yes", "Попадают под условие акции"),
            ("no", "Нет"),
        )

    def queryset(
            self, request: WSGIRequest, queryset: QuerySet[Product]
    ) -> QuerySet[Product]:
        if self.value() == "yes":
            return queryset.exclude(
                variants__sale_price__in=[None, decimal.Decimal("0.00")]
            )
        elif self.value() == "no":
            return queryset.filter(
                variants__sale_price__in=[None, decimal.Decimal("0.00")]
            )


class CreationMonthFilter(admin.SimpleListFilter):
    title = "Месяц заказа"
    parameter_name = "creation_month"

    def lookups(self, request: WSGIRequest, model_admin: ModelAdmin) -> list:
        queryset = model_admin.get_queryset(request)
        months = (
            queryset.annotate(month=TruncMonth("order_date")).values("month").distinct()
        )
        russian_months = [
            (
                month["month"].strftime("%Y-%m"),
                _(calendar.month_name[int(month["month"].strftime("%m"))]),
            )
            for month in months
        ]
        return russian_months

    def queryset(self, request: WSGIRequest, queryset: QuerySet) -> QuerySet:
        if self.value():
            year, month = self.value().split("-")
            queryset.filter(order_date__year=year, order_date__month=month)
            return queryset.filter(order_date__year=year, order_date__month=month)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "image_tag", "image")
    readonly_fields = ("id", "name", "image_tag")
    form = BrandAdminForm
    fieldsets = (
        (
            "Общее",
            {
                "fields": (
                    "name",
                    "image_tag",
                    "image"
                )
            }
        ),
        (
            "SEO",
            {
                "fields": (
                    "page_title",
                    "meta_description",
                    "h1",
                    "text_under_title",
                    "text_under_product",
                    "breadcrumb"
                )
            }
        )
    )

    @admin.display(description="Логотип бренда")
    def image_tag(self, obj: Brand) -> SafeString | str:
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" alt="">')
        return ""


@admin.register(Category)
class CategoryDraggableMPTTAdmin(DraggableMPTTAdmin):
    mptt_level_indent = 50
    form = CategoryAdminForm
    list_display = (
        "tree_actions",
        "indented_title",
        "image_tag",
        "is_active",
        "parent",
    )
    readonly_fields = ('image_tag',)
    list_display_links = ("indented_title",)
    fields = ("name", "is_active", "category_image", "image_tag",)

    def something(self, instance: Category) -> SafeString | str:
        return format_html(
            '<div style="text-indent:{}px">{}</div>',
            instance._mpttfield("level") * self.mptt_level_indent,
            instance.name,
        )

    @admin.display(description="")
    def image_tag(self, obj: Category) -> SafeString | str:
        if obj.category_image:
            return mark_safe(
                f'<img src="{obj.category_image.url}" weight="50" height="50"/>'
            )
        return ""


class VariantAdminInline(StackedInline):
    model = Variant
    verbose_name = "Вариант"
    verbose_name_plural = "Варианты"
    ordering = ("-archived",)
    extra = 0
    can_delete = False
    show_change_link = True
    fieldsets = (
        (
            "Общее",
            {
                "fields": (
                    "archived",
                    "name",
                    "variant_characteristics",
                    "price",
                    "sale_price",
                    "to_order",
                    "code",
                    "stock",
                    "reserve",
                    "quantity",
                    "is_active",
                )
            },
        ),
    )
    readonly_fields = (
        "archived",
        "name",
        "price",
        "sale_price",
        "code",
        "variant_characteristics",
        "stock",
        "reserve",
        "quantity",
    )

    def has_add_permission(self, request: WSGIRequest, obj: Variant) -> bool:
        return True

    @admin.display(description="Характеристики")
    def variant_characteristics(self, obj: Variant) -> str | SafeString:
        rows = []
        for characteristic in obj.characteristics.all():
            value = characteristic.value
            try:
                value = json.loads(characteristic.value.replace("'", '"'))["name"]
            except BaseException:
                pass
            rows.append(
                f"</tr><tr><td>{characteristic.type.name}</td><td>{value}</td></tr>"
            )
        table = (
            f'<table class="table table-striped"><thead><tr><th>Характеристика</th><th>Значение</th>'
            f'{"".join(rows)}</thead></table>'
        )
        return mark_safe(table)


class TagInline(StackedInline):
    model = Tag.product.through
    extra = 0
    verbose_name = "Тег"
    verbose_name_plural = "Теги"

    def get_formset(
            self, request: WSGIRequest, obj: Tag = None, **kwargs: dict
    ) -> BaseModelFormSet:
        formset = super().get_formset(request, obj, **kwargs)
        formset.form.base_fields["tag"].label = "Тег"
        return formset


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "priority")
    readonly_fields = ("product",)
    fieldsets = (
        (
            'Общее',
            {
                'fields': ("name", "priority")
            }
        ),
        (
            "SEO",
            {
                "fields": (
                    "page_title",
                    "meta_description",
                    "h1",
                    "breadcrumb"
                )
            }
        )
    )


class CrossaleInline(admin.StackedInline):
    model = Product.crossale.through
    verbose_name = "Рекомендуемый товар"
    verbose_name_plural = "Рекомендуемые товары"
    extra = 0
    fk_name = "product"


class ProductImageInline(admin.StackedInline):
    model = ProductImage
    extra = 0
    ordering = ("priority",)
    list_display = ("image_tag", "miniature_tag", "is_preview",)
    fields = ("image_tag", "miniature_tag", "is_preview",)
    readonly_fields = ("image_tag", "miniature_tag", "is_preview")
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request: WSGIRequest, obj: Variant) -> bool:
        return False

    @admin.display(description="Изображение")
    def image_tag(self, obj: ProductImage) -> SafeString | str:
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" weight="200" height="200"/>')
        return ""

    @admin.display(description="Миниатюра")
    def miniature_tag(self, obj: ProductImage) -> SafeString | str:
        if obj.miniature:
            return mark_safe(
                f'<img src="{obj.miniature.url}" weight="100" height="100"/>'
            )
        return ""

    @admin.display(description="Превью")
    def is_preview(self, obj: ProductImage) -> SafeString:
        if obj.priority == 0:
            return mark_safe('<img src="/static/admin/img/icon-yes.svg" alt="True">')
        return mark_safe('<img src="/static/admin/img/icon-no.svg" alt="False">')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [
        VariantAdminInline,
        TagInline,
        ProductImageInline,
        CrossaleInline
    ]
    actions = (make_to_order, "make_is_active", "exclude_from_filters", "show_determinate_size")
    fieldsets = (
        (
            "Общее",
            {
                "fields": (
                    "name",
                    "description",
                    "category",
                    "label",
                    "article",
                    "archived",
                    "is_active",
                )
            },
        ),
        (
            "Дополнительные характеристики",
            {
                "fields": (
                    "brand",
                    "characteristics",
                    "code",
                    "weight",
                    "volume",
                )
            },
        ),
    )

    readonly_fields = (
        "name",
        "description",
        "article",
        "archived",
        "article",
        "archived",
        "brand",
        "characteristics",
        "code",
        "weight",
        "volume",
        "updated_at",
    )
    list_display = ("name", "miniature_tag", "article", "label", "is_active", "updated_at")
    list_filter = ("category", "tags", NoVariantFilter, ImageFilter, DiscountFilter)
    search_fields = (
        "name",
        "article",
        "code",
        "id",
        "description",
        "characteristics__value",
    )
    list_max_show_all = 10000


    @admin.display(description="Миниатюра")
    def miniature_tag(self, obj: Product) -> str | SafeString:
        image = obj.images.filter(priority=0).first()
        if image and image.miniature:
            return mark_safe(f'<img src="{image.miniature.url}" alt="" width="60">')

    @admin.display(description="Характеристики")
    def characteristics(self, obj: Product) -> str | SafeString:
        rows = []
        for characteristic in obj.characteristics.all():
            value = characteristic.value
            try:
                value = json.loads(characteristic.value.replace("'", '"'))["name"]
            except BaseException:
                pass
            rows.append(
                f"</tr><tr><td>{characteristic.type.name}</td><td>{value}</td></tr>"
            )
        table = (
            f'<table class="table table-striped"><thead><tr><th>Характеристика</th>'
            f'<th>Значение</th>{"".join(rows)}</thead></table>'
        )
        return mark_safe(table)

    @admin.action(description="Активировать товар")
    def make_is_active(self, request: WSGIRequest, queryset: QuerySet[Product]) -> None:
        """
        Активирует выбранные товары и варианты товаров у которых назначена категория
        """
        variants = Variant.objects.filter(
            product_id__in=queryset.values_list("id", flat=True)
        )
        queryset.update(is_active=True)
        variants.update(is_active=True)

    @admin.action(description='Добавить кнопку “Определить размер”')
    def show_determinate_size(self, request: WSGIRequest, queryset: QuerySet[Product]) -> None:
        queryset.update(determine_size=True)

    @admin.action(description="Исключить из фильтров по размеру")
    def exclude_from_filters(self, request: WSGIRequest, queryset: QuerySet[Product]) -> None:
        queryset.update(exclude_from_filter=True)

    def get_queryset(self, request: WSGIRequest) -> QuerySet:
        qs = self.model._default_manager.get_queryset().filter(
            Q(category__isnull=False)
            & Q(images__isnull=False)
            & Q(weight__gt=0)
            & Q(archived=False)
        ).distinct()
        variants_null_price_ids = Variant.objects.filter(
            Q(product__id__in=qs.values_list("id", flat=True))
            & Q(Q(price=0) & Q(archived=False))
        ).values_list('product_id', flat=True)

        qs = qs.exclude(id__in=variants_null_price_ids)
        return qs


@admin.register(ShowcaseProduct)
class ShowcaseProductAdmin(admin.ModelAdmin):
    inlines = [VariantAdminInline, TagInline, CrossaleInline, ProductImageInline]
    actions = (make_to_order, "make_is_active", "set_category",)
    fieldsets = (
        (
            "Общее",
            {
                "fields": (
                    "name",
                    "description",
                    "category",
                    "label",
                    "article",
                    "archived",
                    "is_active",
                )
            },
        ),
        (
            "Дополнительные характеристики",
            {
                "fields": (
                    "brand",
                    "characteristics",
                    "code",
                    "weight",
                    "volume",
                )
            },
        ),
    )
    readonly_fields = (
        "name",
        "description",
        "article",
        "archived",
        "article",
        "archived",
        "brand",
        "characteristics",
        "code",
        "volume",
        "miniature_tag",
    )
    list_display = ("name", "miniature_tag", "article", "label", "is_active")
    list_filter = ("category", "tags", NoVariantFilter, ImageFilter, DiscountFilter)
    search_fields = (
        "name",
        "article",
        "code",
        "id",
        "description",
        "characteristics__value",
    )
    list_max_show_all = 10000

    @admin.action(description="Активировать товар")
    def make_is_active(self, request: WSGIRequest, queryset: QuerySet[Product]) -> None:
        """
        Активирует выбранные товары и варианты товаров у которых назначена категория
        """
        variants = Variant.objects.filter(
            product_id__in=queryset.values_list("id", flat=True)
        )
        correct_products = queryset.filter(
            category__isnull=False
        )
        correct_products.update(is_active=True)
        variants.update(is_active=True)

    @admin.display(description="Миниатюра")
    def miniature_tag(self, obj: Product) -> str | SafeString:
        image = obj.images.filter(priority=0).first()
        if image:
            if image.miniature:
                return mark_safe(f'<img src="{image.miniature.url}" alt="" width="60">')

    @admin.display(description="Характеристики")
    def characteristics(self, obj: Product) -> str | SafeString:
        rows = []
        for characteristic in obj.characteristics.all():
            value = characteristic.value
            try:
                value = json.loads(characteristic.value.replace("'", '"'))["name"]
            except BaseException:
                pass
            rows.append(
                f"</tr><tr><td>{characteristic.type.name}</td><td>{value}</td></tr>"
            )
        table = (
            f'<table class="table table-striped"><thead><tr><th>Характеристика</th>'
            f'<th>Значение</th>{"".join(rows)}</thead></table>'
        )
        return mark_safe(table)

    def get_queryset(self, request: WSGIRequest) -> QuerySet:
        qs = self.model._default_manager.get_queryset().filter(
            Q(weight=0)
            | Q(category__isnull=True)
            | Q(archived=True)
            | Q(images__isnull=True)
            | Q(Q(variants__price=0) & Q(variants__archived=False))
        ).distinct()
        return qs

    @admin.action(description="Назначить категории")
    def set_category(
            self, request: WSGIRequest, queryset: QuerySet[Product]
    ) -> HttpResponseRedirect or HttpResponse:
        weight_is_null: QuerySet = queryset.filter(weight=0)
        price_is_null: QuerySet = queryset.filter(variants__price=0).distinct('pk')
        if weight_is_null.exists():
            self.message_user(
                request,
                f"У товаров {', '.join([prod.__str__() for prod in weight_is_null.all()])} \n не указан вес",
            )
        if price_is_null.exists():
            self.message_user(
                request,
                f"У товаров {', '.join([prod.__str__() for prod in price_is_null.all()])} \n не указана цена",
                level='error'
            )

        form = None
        if "apply" in request.POST:
            categories: TreeQuerySet[Category] = Category.objects.filter(
                id__in=request.POST.getlist("category")
            )
            list_categories = list(categories.values_list("id", flat=True))
            for element in queryset:
                element.category.set(list_categories)
            self.message_user(
                request,
                f"Категории ({', '.join([category.__str__() for category in categories])}) назначена к {queryset.count()} товарам.",
            )
            return HttpResponseRedirect(request.get_full_path())
        if not form:
            form = SetCategoryForm(
                initial={
                    "_selected_action": request.POST.getlist("_selected_action"),
                }
            )
        return render(
            request,
            "set_category.html",
            {
                "form": form,
                "title": "Изменение категорий",
                "action": "set_category",
            },
        )


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "priority",
        "color_label",
    )
    fields = ("name", "priority", "color", 'type_label')

    @admin.display(description="Цвет")
    def color_label(self, obj: Label) -> SafeString:
        return mark_safe(
            f'<div style="width: 20px; height: 20px; background-color: {obj.color};"></div>'
        )

    def has_delete_permission(self, request: WSGIRequest, obj: Label = None) -> bool:
        if obj:
            if obj.name in ("Акция", "Хит продаж", "Новинка"):
                return False
        return True


class ItemBasketInline(ReadOnlyStackedInline):
    model = ItemBasket
    extra = 0
    fields = (
        "code",
        "name",
        "article",
        "price",
        "sale_price",
        "quantity",
        "item_total_cost",
        "item_total_cost_with_discount",
        "item_discount",
        "variant_product",
        "basket",
        "get_label",
        "get_size",
        "image_tag",
    )
    readonly_fields = (
        "code",
        "name",
        "article",
        "price",
        "sale_price",
        "quantity",
        "item_total_cost",
        "item_total_cost_with_discount",
        "item_discount",
        "variant_product",
        "basket",
        "get_label",
        "get_size",
        "image_tag",
    )

    @admin.display(description="Лейбл")
    def get_label(self, obj: ItemBasket) -> str:
        return obj.variant_product.product.label.name

    @admin.display(description="Размер")
    def get_size(self, obj: ItemBasket) -> str:
        return (
            obj.variant_product.characteristics.filter(type__name="Размер")
            .first()
            .value
        )

    @admin.display(description="Изображение товара")
    def image_tag(self, obj: ItemBasket) -> SafeString:
        image = obj.variant_product.product.images.filter(priority=0).first().miniature
        if image:
            return mark_safe(f'<img src="{image.url}" weight="100" height="100" alt="">')


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    inlines = (ItemBasketInline,)
    ordering = ('-order_date',)
    list_display = (
        "user",
        "order_date",
        "payment_status",
        "total_cost",
        "order_state",
    )
    list_filter = (
        "user__username",
        "payment_status",
        "order_state",
        CreationMonthFilter,
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__username",
        "order_number",
        "order_name",
    )
    readonly_fields = (
        "order_number",
        "user",
        "order_date",
        "order_state",
        "status",
        "payment_status",
        "payment_method",
        "city",
        "country",
        "address",
        "customer_name",
        "customer_surname",
        "customer_phone",
        "customer_email",
        "total_cost",
        "without_discount",
        "with_discount",
        "discount",
        "count_of_products",
        "unparsed_parts"
    )
    fieldsets = (
        (
            "Основное",
            {
                "fields": (
                    "order_name",
                    "order_number",
                    "user",
                    "order_date",
                    "order_state",
                    "status",
                    "payment_status",
                    "payment_method",
                    "city",
                    "country",
                    "address",
                    "order_link",
                    "unparsed_parts",
                )
            },
        ),
        (
            "Данные получателя",
            {
                "fields": (
                    "customer_name",
                    "customer_surname",
                    "customer_phone",
                    "customer_email",
                )
            },
        ),
        (
            "Итого",
            {
                "fields": (
                    "total_cost",
                    "without_discount",
                    "with_discount",
                    "discount",
                    "count_of_products",
                )
            },
        ),
    )

    def get_queryset(self, request: WSGIRequest) -> QuerySet:
        return self.model._default_manager.get_queryset().exclude(
            status=BasketStatus.IS_ACTIVE
        )

    def has_add_permission(self, request: WSGIRequest) -> bool:
        return False

    @admin.display(description="Количество вариантов товаров")
    def count_of_products(self, obj: Basket) -> int:
        return obj.item_baskets.all().count()


    @admin.display(description="Сумма без скидки")
    def without_discount(self, obj: Basket) -> Decimal:
        data_cost = obj.item_baskets.get_cost_info()
        return data_cost.aggregate(basket_without_discount=Sum("without_discount"))[
            "basket_without_discount"
        ]

    @admin.display(description="Сумма со скидкой")
    def with_discount(self, obj: Basket) -> Decimal:
        data_cost = obj.item_baskets.get_cost_info().aggregate(
            basket_with_discount=Sum("without_discount") - Sum("item_total_discount")
        )
        return data_cost["basket_with_discount"]

    @admin.display(description="Итоговая скидка")
    def settlement_discount(self, obj: Basket) -> Decimal | None:
        if self.with_discount(obj) and self.without_discount:
            return self.with_discount(obj) - self.without_discount(obj)
        return None


class ActiveItemBasketInline(ReadOnlyStackedInline):
    model = ItemBasket
    extra = 0
    fields = (
        "variant_name",
        "code",
        "get_size",
        "get_label",
        "quantity",
        "variant_code",
        "article",
        "variant_price",
        "variant_sale_price",
        "variant_miniature",
    )
    readonly_fields = (
        "variant_name",
        "get_size",
        "get_label",
        "quantity",
        "variant_code",
        "article",
        "variant_price",
        "variant_sale_price",
        "variant_miniature",
    )

    @admin.display(description="Лейбл")
    def get_label(self, obj: ItemBasket) -> str:
        return obj.variant_product.product.label.name

    @admin.display(description='Название')
    def variant_name(self, obj: ItemBasket) -> str:
        return obj.variant_product.name

    @admin.display(description='артикул товара')
    def article(self, obj: ItemBasket) -> str:
        return obj.variant_product.product.article

    @admin.display(description='Код варианта')
    def variant_code(self, obj: ItemBasket) -> str:
        return obj.variant_product.code

    @admin.display(description="Размер")
    def get_size(self, obj: ItemBasket) -> str:
        return obj.variant_product.characteristics.filter(type__name="Размер").first().value

    @admin.display(description="Цена")
    def variant_price(self, obj: ItemBasket) -> Decimal:
        return obj.variant_product.price

    @admin.display(description="Цена со скидкой")
    def variant_sale_price(self, obj: ItemBasket) -> Decimal:
        return obj.variant_product.sale_price

    @admin.display(description="Миниатюра")
    def variant_miniature(self, obj: ItemBasket) -> SafeString | str:
        image = obj.variant_product.product.images.filter(priority=0).first().miniature
        if image:
            return mark_safe(f'<img src="{image.url}" weight="100" height="100"/>')
        return "-"


@admin.register(ActiveBasket)
class ActiveBasketAdmin(BasketAdmin):
    inlines = (ActiveItemBasketInline,)
    readonly_fields = (
        "update_at",
        "count_of_products",
        "without_discount",
        "with_discount",
        "settlement_discount",
        "settlement_cost_with_discount",
        "status",
        "customer_name",
        "customer_surname",
        "customer_phone",
        "customer_email",
        "user",
    )

    list_display = ("user", "status", "count_of_products", "settlement_cost_with_discount", "update_at")
    list_filter = ("user__username",)
    search_fields = ("user__first_name", "user__last_name", "user__username")
    change_list_template = "active_basket_template.html"

    fieldsets = (
        (
            "Основное",
            {
                "fields": (
                    "user",
                    "status",
                    "order_date",
                    "address",
                    "update_at"
                )
            },
        ),
        (
            "Данные получателя",
            {
                "fields": (
                    "customer_name",
                    "customer_surname",
                    "customer_phone",
                    "customer_email",
                )
            },
        ),
        (
            "Итого",
            {
                "fields": (
                    "without_discount",
                    "settlement_discount",
                    "settlement_cost_with_discount",
                    "count_of_products",
                )
            },
        ),
    )

    def get_queryset(self, request: WSGIRequest) -> QuerySet:
        return self.model._default_manager.get_queryset().filter(
            status=BasketStatus.IS_ACTIVE
        ).exclude(item_baskets__isnull=True)

    def changelist_view(self, request, extra_context=None) -> HttpResponse:
        active_baskets = self.get_queryset(request)
        total_baskets_cost = active_baskets.aggregate(
            price_variants_total_cost=Sum(
                F('item_baskets__variant_product__price') * F('item_baskets__quantity'),
                filter=Q(item_baskets__variant_product__sale_price=0)
            ),
            sale_price_variants_total_cost=Sum(
                F('item_baskets__variant_product__sale_price') * F('item_baskets__quantity'),
                filter=Q(item_baskets__variant_product__sale_price__gt=0)
            ),
        )
        baskets_total_cost = dict(total_baskets_cost)
        if baskets_total_cost.get('price_variants_total_cost'):
            baskets_price_total_cost = baskets_total_cost.get('price_variants_total_cost')
        else:
            baskets_price_total_cost = 0
        if baskets_total_cost.get('sale_price_variants_total_cost'):
            baskets_sale_price_total_cost = baskets_total_cost.get('sale_price_variants_total_cost')
        else:
            baskets_sale_price_total_cost = 0
        extra_context = {'total_price': baskets_price_total_cost + baskets_sale_price_total_cost}
        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request: WSGIRequest) -> bool:
        return False

    @admin.display(description="Итоговая сумма без скидки")
    def without_discoint(self, request, obj: Product):
        data_cost = obj.item_baskets.get_settlement_cost_info()
        return data_cost.aggregate(
            basket_without_discount=Sum("settlement_total_price")
        )["basket_without_discount"]

    @admin.display(description="Размер скидки")
    def settlement_discount(self, obj: ActiveBasket) -> Decimal | None:
        data_cost = obj.item_baskets.get_settlement_cost_info()
        return data_cost.aggregate(basket_discount=Sum("settlement_discount"))[
            "basket_discount"
        ]

    @admin.display(description="Итоговая сумма со скидкой")
    def settlement_cost_with_discount(self, obj: ActiveBasket) -> Decimal | None:
        data_cost = obj.item_baskets.get_settlement_cost_info().aggregate(
            basket_with_discount=Sum("settlement_total_price")
                                 - Sum("settlement_discount")
        )["basket_with_discount"]
        return data_cost

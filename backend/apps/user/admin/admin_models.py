from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.models import Group as DefaultGroup
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Field, ManyToManyField, QuerySet

from apps.market.models import Basket, Favorite
from apps.user.enum import PaymentType
from apps.user.models import Group, SMSKey, User
from utils.abstractions.admin import AbstractAdmin


class BasketInline(admin.StackedInline):
    model = Basket
    extra = 0


class FavoriteInline(admin.StackedInline):
    model = Favorite
    extra = 0
    verbose_name = "Избранный товар"
    verbose_name_plural = "Избранные товары"


@admin.register(User)
class UserAdmin(DefaultUserAdmin, AbstractAdmin):
    inlines = (FavoriteInline,)
    fieldsets = (
        ("Общее", {"fields": ("username", "email", "password")}),
        (
            "Личная информация",
            {
                "fields": (
                    "first_name",
                    "last_name",
                )
            },
        ),
        (
            "Разрешения",
            {
                "fields": (
                    "is_active",
                    "is_admin",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Способы платежа",
            {
                "fields": ("is_dealer", "payment_method", "payment_type_items"),
            },
        ),
        (
            "Поля, доступные только для чтения",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                )
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
    )
    readonly_fields = (
        "last_login",
        "date_joined",
        "payment_type_items",
    )
    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "is_dealer",
        "payment_method",
        "last_login"
    )
    list_filter = ("username", "last_name", "first_name")
    search_fields = (
        "username",
        "email",
        "first_name",
        "second_name",
        "last_name",
    )
    ordering = ("date_joined",)

    @admin.display(description="Варианты оплаты")
    def payment_type_items(self, obj: User) -> str:
        if obj.payment_method == PaymentType.PREPAID:
            return "Онлайн на сайте (Эквайринг Тинькофф), Наличными при получении, Картой при получении"
        return "Переводом на карту по истечении 30 дней с момента заказа"


admin.site.unregister(DefaultGroup)


@admin.register(Group)
class GroupAdmin(AbstractAdmin):
    search_fields = ("name",)
    ordering = ("name",)
    filter_horizontal = ("permissions",)
    fieldsets = (
        (
            "Общее",
            {
                "fields": (
                    "name",
                    "permissions",
                )
            },
        ),
    )

    def formfield_for_manytomany(
        self,
        db_field: ManyToManyField,
        request: WSGIRequest | None = None,
        queryset: QuerySet | None = None,
        **kwargs: dict
    ) -> Field:
        if db_field.name == "permissions":
            queryset = queryset or db_field.remote_field.model.objects
            kwargs["queryset"] = queryset.select_related("content_type")
        return super().formfield_for_manytomany(db_field, request=request, **kwargs)


@admin.register(SMSKey)
class SMSKeyAdmin(admin.ModelAdmin):
    list_display = ('key', 'user', 'update_at')
    readonly_fields = ('update_at', 'user')

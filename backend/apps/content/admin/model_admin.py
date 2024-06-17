from django.contrib import admin
from django.utils.safestring import SafeString, mark_safe
from solo.admin import SingletonModelAdmin

from apps.content.admin.forms import (AboutAdminForm,
                                      ContactAdminForm,
                                      FAQAdminForm,
                                      ReturnConditionsFormAdmin)
from apps.content.models import (FAQ, About, AboutImage, Banner,
                                 Contact, DeliveryMethod, Documents, Header,
                                 RecipientEmail, ReturnConditions)

from utils.abstractions.admin import AbstractAdmin


@admin.register(Documents)
class DocumentsAdmin(admin.ModelAdmin):
    pass


class AboutImageInline(admin.StackedInline):
    model = AboutImage
    extra = 0


@admin.register(About)
class AboutAdmin(SingletonModelAdmin):
    form = AboutAdminForm


@admin.register(Banner)
class BannerAdmin(AbstractAdmin):
    list_display = (
        "name",
        "is_active",
        "image_tag",
        "mobile_image_tag",
        "priority",
        "banner_link",
    )
    list_display_links = ("name", "is_active", "image_tag", "mobile_image_tag")
    fields = (
        "name",
        "image_tag",
        "banner_image",
        "mobile_image_tag",
        "adaptive_image",
        "priority",
        "is_active",
        "banner_link",
    )
    readonly_fields = ("image_tag", "mobile_image_tag")

    @admin.display(description="")
    def image_tag(self, obj: Banner) -> SafeString | str:
        if obj.banner_image:
            return mark_safe(
                f'<img src="{obj.banner_image.url}" weight="50" height="50"/>'
            )
        return ""

    @admin.display(description="")
    def mobile_image_tag(self, obj: Banner) -> SafeString | str:
        if obj.adaptive_image:
            return mark_safe(
                f'<img src="{obj.adaptive_image.url}" weight="50" height="50"/>'
            )
        return ""


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "priority")
    form = FAQAdminForm


class RecipientEmailInline(admin.StackedInline):
    model = RecipientEmail
    extra = 0


@admin.register(Contact)
class ContactAdmin(SingletonModelAdmin):
    inlines = (RecipientEmailInline, )
    form = ContactAdminForm


@admin.register(ReturnConditions)
class ReturnConditionsAdmin(SingletonModelAdmin):
    form = ReturnConditionsFormAdmin


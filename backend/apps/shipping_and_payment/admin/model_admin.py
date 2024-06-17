import logging

from django.contrib import admin
from solo.admin import SingletonModelAdmin

from apps.shipping_and_payment.models import Provider


@admin.register(Provider)
class ProviderAdmin(SingletonModelAdmin):
    pass

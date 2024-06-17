from rest_framework import serializers

from apps.shipping_and_payment.models import Provider


class ProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provider
        fields = "__all__"

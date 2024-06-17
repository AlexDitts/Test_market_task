from apps.shipping_and_payment.api.serializers import ProviderSerializer
from apps.shipping_and_payment.models import Provider
from utils.abstractions.viewset import AbstractSingleView


class ProviderViewSet(AbstractSingleView):
    queryset = Provider.objects.all()
    serializer_class = ProviderSerializer

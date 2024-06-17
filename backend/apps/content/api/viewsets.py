from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from apps.content.api.serializers import (AboutSerializer,
                                          BannerSerializer,
                                          ContactSerializer,
                                          DeliveryMethodSerializer,
                                          DocumentSerializer, FAQSerializer,
                                          ReturnConditionsSerializer,
                                          )
from apps.content.models import (FAQ, About, Banner, Contact, DeliveryMethod,
                                 Documents, Header, ReturnConditions)
from utils.abstractions.viewset import AbstractSingleView


class DocumentsViewSet(AbstractSingleView):
    queryset = Documents.objects.all()
    serializer_class = DocumentSerializer


class AboutViewSet(AbstractSingleView):
    queryset = About.objects.all()
    serializer_class = AboutSerializer


class BannerViewSet(ListModelMixin,
                    RetrieveModelMixin,
                    GenericViewSet):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ('name', 'is_active')


class ContactViewSet(AbstractSingleView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer


class DeliveryMethodViewSet(ReadOnlyModelViewSet):
    queryset = DeliveryMethod.objects.all()
    serializer_class = DeliveryMethodSerializer


class FAQViewSet(ReadOnlyModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer


class ReturnConditionsViewSet(AbstractSingleView):
    queryset = ReturnConditions.objects.all()
    serializer_class = ReturnConditionsSerializer

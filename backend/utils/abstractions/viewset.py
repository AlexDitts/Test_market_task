from typing import Any

from django.http import HttpRequest
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet


class AbstractModelViewSet(ModelViewSet):
    """
    Base class from which all viewset classes should be inherited,
    in order to have an option to add behavior to the group of viewsets.
    """
    ...


class AbstractSingleView(ListModelMixin, GenericViewSet):
    """Представление для модели About"""

    queryset = None
    serializer_class = None

    def list(self, request: HttpRequest, *args: Any, **kwargs: Any) -> Response:
        if not self.get_queryset().exists():
            return Response(status=404, data={'message': 'ObjectDoesNotExist'})
        instance = self.get_queryset().get()
        serializer = self.get_serializer(instance=instance)
        return Response(status=200, data=serializer.data)

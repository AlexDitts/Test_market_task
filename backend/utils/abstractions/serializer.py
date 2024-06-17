from pydantic import BaseModel
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from restdoctor.rest_framework.serializers import (
    PydanticSerializer as BasePydanticSerializer,
)


class AbstractModelSerializer(ModelSerializer):
    """
    Base class from which all serializer classes should be inherited,
    in order to have an option to add behavior to the group of serializers.
    """

    ...


class DateFromDateToSerializer(serializers.Serializer):
    """Сериализатор полей дата начала и окончания действия."""

    date_from = serializers.DateField(
        format="%Y-%m-%d", required=False, allow_null=True
    )
    date_to = serializers.DateField(format="%Y-%m-%d", required=False, allow_null=True)


class PydanticSerializer(BasePydanticSerializer):
    @property
    def pydantic_instance(self) -> BaseModel:
        if not hasattr(self, "_validated_data"):
            msg = "You must call `.is_valid()` before accessing `.pydantic_instance`."
            raise AssertionError(msg)
        return self._pydantic_instance


class PydanticSerializerWithAliases(BasePydanticSerializer):
    def pydantic_use_aliases(self) -> bool:
        return True

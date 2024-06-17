from django.db.models import Model, Field, DateField, DateTimeField, TimeField
from rest_framework.utils import model_meta
from restdoctor.utils.custom_types import GenericContext

from utils.dto import DjangoModel


def get_all_fields_names(*, model: type[Model]) -> list[str]:
    return [field.name for field in model._meta.fields]


def get_updated_fields(*, model: type[Model], data: dict) -> dict:
    return {
        element: data.get(element)
        for element in filter(
            lambda field: field in get_all_fields_names(model=model), data
        )
    }


def model_update(*, instance: Model, updated_fields: dict) -> None:
    for key, value in updated_fields.items():
        setattr(instance, key, value)
    instance.save()


def field__is_auto_now(*, field: Field) -> bool:
    return isinstance(field, (DateField, DateTimeField, TimeField)) and getattr(
        field, "auto_now", False
    )


def update_model_instance(  # noqa: CAC001 because used DRF realisation
    *,
    instance: DjangoModel,
    validated_data: GenericContext,
    update_fields: list[str] | None = None,
) -> DjangoModel:
    info = model_meta.get_field_info(instance)
    model_fields = instance.__class__._meta.fields
    auto_fields = [
        field.attname for field in model_fields if field__is_auto_now(field=field)
    ]
    # Simply set each attribute on the instance, and then save it.
    # Note that unlike `create_model_instance()` we don't need to treat many-to-many
    # relationships as being a special case. During updates we already
    # have an instance pk for the relationships to be associated with.
    m2m_fields = []
    common_fields = []
    for attr, value in validated_data.items():
        if attr in info.relations and info.relations[attr].to_many:
            m2m_fields.append((attr, value))
        else:
            setattr(instance, attr, value)
            common_fields.append(attr)
    update_fields = update_fields or common_fields
    update_fields += auto_fields
    instance.save(update_fields=update_fields)
    # Note that many-to-many fields are set after updating instance.
    # Setting m2m fields triggers signals which could potentially change
    # updated instance and we do not want it to collide with update_model_instance()
    for attr, value in m2m_fields:
        field = getattr(instance, attr)
        field.set(value)
    return instance

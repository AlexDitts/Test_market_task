from django.core.exceptions import ValidationError


def validate_nonzero(value: int) -> None:
    if value == 0:
        raise ValidationError('Значение не может быть равно 0.')

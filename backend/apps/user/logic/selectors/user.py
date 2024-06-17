from django.db.models import QuerySet

from apps.user.models import User


def user__all() -> QuerySet[User]:
    return User.objects.all()


def users__by_pk(*, queryset: QuerySet[User] | None = None, pk: int | str) -> QuerySet[User]:
    if not queryset:
        queryset = user__all()
    return queryset.filter(pk=pk)


def user__by_pk(*, queryset: QuerySet[User] | None = None, pk: int | str) -> QuerySet[User]:
    return users__by_pk(queryset=queryset, pk=pk).first()


def users__by_is_active(*, queryset: QuerySet[User] | None = None, is_active: bool = True) -> QuerySet[User]:
    if not queryset:
        queryset = user__all()
    return queryset.filter(is_active=is_active)

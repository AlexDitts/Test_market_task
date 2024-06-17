from django.db.models import QuerySet

from apps.user.models import Group


def group__all() -> QuerySet[Group]:
    return Group.objects.all()


def groups__by_pk(*, queryset: QuerySet[Group] | None = None, pk: int | str) -> QuerySet[Group]:
    if not queryset:
        queryset = group__all()
    return queryset.filter(pk=pk)


def group__by_pk(*, queryset: QuerySet[Group] | None = None, pk: int | str) -> QuerySet[Group]:
    return groups__by_pk(queryset=queryset, pk=pk).first()

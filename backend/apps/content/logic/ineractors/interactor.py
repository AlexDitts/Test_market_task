from django.db.models import QuerySet

from apps.market.models import Category


def apportioned_children(children: QuerySet[Category]) -> list | dict:
    if not children or len(children) == 0:
        return {'children': None}
    return [
        {
            'cat_id': category.id,
            'cat_is_active': category.is_active,
            'cat_show_to_header': category.show_in_header,
            'cat_name': category.name,
            'children': apportioned_children(category.get_children())
        } for num, category in enumerate(children)
    ]

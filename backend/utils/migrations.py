from __future__ import annotations

import datetime
import uuid
from typing import TYPE_CHECKING, Callable, List, Tuple, Type

from django.contrib.auth.management import create_permissions
from django.contrib.auth.models import Permission
from django.core.exceptions import ObjectDoesNotExist
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps
from django.db.models import Count, Q
from django.db.models.functions import Lower
from django.utils.timezone import localtime

if TYPE_CHECKING:
    from django.contrib.contenttypes.models import ContentType
    from django.db.models import Model, QuerySet

    from apps.user.models import Group, User


def _process_permissions_types(
        *,
        permission_types: list[str],
        permission_model_class: Permission,
        group_model_class: Group,
        my_user_model_class: User,
        from_content_type: ContentType,
        from_modelname: str,
        to_content_type: ContentType,
        to_modelname: str,
) -> None:
    for permission_type in permission_types:
        try:
            from_permission = permission_model_class.objects.get(
                content_type=from_content_type, codename=f'{permission_type}_{from_modelname}'
            )
            to_permission = permission_model_class.objects.get(
                content_type=to_content_type, codename=f'{permission_type}_{to_modelname}'
            )
        except ObjectDoesNotExist:
            continue

        for group in group_model_class.objects.filter(permissions=from_permission):
            group.permissions.add(to_permission)

        for user in my_user_model_class.objects.filter(user_permissions=from_permission):
            user.user_permissions.add(to_permission)


def create_django_permissions(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None


def copy_permissions_between_models(
        from_model: Tuple[str, str], to_model: Tuple[str, str], permission_types: List[str] = None
) -> Callable:
    if permission_types is None:
        permission_types = ['add', 'change', 'delete', 'view']

    def _copy_permissions_between_models(
            apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
    ) -> None:
        group_model_class = apps.get_model('auth', 'Group')
        permission_model_class = apps.get_model('auth', 'Permission')
        my_user_model_class = apps.get_model('users', 'User')
        content_type_model_class = apps.get_model('contenttypes', 'ContentType')

        from_applabel = from_model[0]
        from_modelname = from_model[1]
        to_applabel = to_model[0]
        to_modelname = to_model[1]

        from_content_type = content_type_model_class.objects.get(
            app_label=from_applabel, model=from_modelname
        )
        to_content_type = content_type_model_class.objects.get(
            app_label=to_applabel, model=to_modelname
        )

        _process_permissions_types(
            permission_types=permission_types,
            permission_model_class=permission_model_class,
            group_model_class=group_model_class,
            my_user_model_class=my_user_model_class,
            from_content_type=from_content_type,
            from_modelname=from_modelname,
            to_content_type=to_content_type,
            to_modelname=to_modelname,
        )

    return _copy_permissions_between_models


def copy_permissions_between_apps(
        from_app: str, to_app: str, model_names: List[str] = None
) -> Callable:
    def _copy_permissions_between_apps(
            apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
    ) -> None:
        content_type_model_class = apps.get_model('contenttypes', 'ContentType')
        permission_model_class = apps.get_model('auth', 'Permission')

        content_type_qs = content_type_model_class.objects.filter(app_label=to_app)
        if model_names is not None:
            content_type_qs = content_type_qs.filter(model__in=model_names)

        for new_content_type in content_type_qs:
            try:
                old_content_type = content_type_model_class.objects.get(
                    app_label=from_app, model=new_content_type.model
                )
            except ObjectDoesNotExist:
                continue

            copy_permissions_between_content_types(
                from_content_type=old_content_type,
                to_content_type=new_content_type,
                permission_model_class=permission_model_class,
            )

    return _copy_permissions_between_apps


def copy_permissions_between_content_types(
        from_content_type: ContentType,
        to_content_type: ContentType,
        permission_model_class: Type[Model],
) -> None:
    for old_permission in permission_model_class.objects.filter(
            content_type=from_content_type
    ).prefetch_related('group_set', 'user_set'):
        try:
            new_permission = permission_model_class.objects.get(
                content_type=to_content_type, codename=old_permission.codename
            )
        except ObjectDoesNotExist:
            new_permission = permission_model_class.objects.create(
                content_type=to_content_type, codename=old_permission.codename
            )

        for group in old_permission.group_set.all():
            group.permissions.add(new_permission)
        for user in old_permission.user_set.all():
            user.user_permissions.add(new_permission)


def grant_permissions(  # noqa: CAC002, CAC001, CCR001, C901
        group_names: List[str],
        app_label: str = None,
        models: List[str] = None,
        codenames: List[str] = None,
        codename_preffixes: List[str] = None,
        users: List[str] = None,
        flush: bool = False,
) -> Callable:
    if users is None:
        users = []

    def _grant_permissions(  # noqa: CAC001, CCR001
            apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
    ) -> None:
        permission_model_class = apps.get_model('auth', 'Permission')
        group_model_class = apps.get_model('auth', 'Group')
        my_user_model_class = apps.get_model('users', 'User')
        permission_qs = _get_permission_qs(
            permission_model_class, app_label, models, codenames, codename_preffixes
        )
        if not flush:
            for name in group_names:
                if not group_model_class.objects.filter(name=name).exists():
                    group = group_model_class.objects.create(name=name)
                    group.save()
                    group.permissions.add(*permission_qs)
            else:
                for group in group_model_class.objects.filter(name__in=group_names):
                    group.permissions.add(*permission_qs)

            for user in my_user_model_class.objects.filter(email__in=users):
                user.user_permissions.add(*permission_qs)
        else:
            for name in group_names:
                if not group_model_class.objects.filter(name=name).exists():
                    group = group_model_class.objects.create(name=name)
                    group.save()
                    group.permissions.set([])
            else:
                for group in group_model_class.objects.filter(name__in=group_names):
                    group.permissions.set([])

            for user in my_user_model_class.objects.filter(email__in=users):
                user.user_permissions.set([])

    return _grant_permissions


def _get_permission_qs(
        permission_model_class: Type[Model],
        app_label: str = None,
        models: List[str] = None,
        codenames: List[str] = None,
        codename_preffixes: List[str] = None,
) -> QuerySet:
    if app_label is not None:
        permission_qs = permission_model_class.objects.filter(content_type__app_label=app_label)
    else:
        permission_qs = permission_model_class.objects.all()

    if models is not None:
        permission_qs = permission_qs.filter(content_type__model__in=models)

    if codenames is not None:
        permission_qs = permission_qs.filter(codename__in=codenames)

    if codename_preffixes is not None:
        codename_prefix_q = Q()
        for preffix in codename_preffixes:
            codename_prefix_q |= Q(codename__startswith=preffix)
        permission_qs = permission_qs.filter(codename_prefix_q)

    return permission_qs


def migrate_generic_fk_forward(
        from_app: str, to_app: str, model_names: List[str] = None
) -> Callable:
    def _migrate_generic_fk_forward(
            apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
    ) -> None:
        content_type_model_class = apps.get_model('contenttypes', 'ContentType')
        models_with_generic_fk = []
        content_type_qs = content_type_model_class.objects.filter(app_label=to_app)
        if model_names is not None:
            content_type_qs = content_type_qs.filter(model__in=model_names)

        for new_content_type in content_type_qs:
            try:
                old_content_type = content_type_model_class.objects.get(
                    app_label=from_app, model=new_content_type.model
                )
            except ObjectDoesNotExist:
                continue

            for model_with_generic_fk in models_with_generic_fk:
                (
                    model_with_generic_fk.objects.filter(content_type=old_content_type).update(
                        content_type=new_content_type
                    )
                )

    return _migrate_generic_fk_forward


def migrate_generic_fk_backward(
        from_app: str, to_app: str, model_names: List[str] = None
) -> Callable:
    def _migrate_generic_fk_backward(
            apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
    ) -> None:
        content_type_model_class = apps.get_model('contenttypes', 'ContentType')
        models_with_generic_fk = []

        content_type_qs = content_type_model_class.objects.filter(app_label=to_app)
        if model_names is not None:
            content_type_qs = content_type_qs.filter(model__in=model_names)

        for new_content_type in content_type_qs:
            try:
                old_content_type = content_type_model_class.objects.get(
                    app_label=from_app, model=new_content_type.model
                )
            except ObjectDoesNotExist:
                continue

            for model_with_generic_fk in models_with_generic_fk:
                (
                    model_with_generic_fk.objects.filter(content_type=new_content_type).update(
                        content_type=old_content_type
                    )
                )

    return _migrate_generic_fk_backward


def create_redirects(from_app: str, to_app: str, model_names: List[str] = None) -> Callable:
    def _create_redirects(apps: StateApps, schema_editor: BaseDatabaseSchemaEditor) -> None:
        content_type_model_class = apps.get_model('contenttypes', 'ContentType')
        redirect_model_class = apps.get_model('redirects', 'Redirect')

        content_type_qs = content_type_model_class.objects.filter(app_label=to_app)
        if model_names is not None:
            content_type_qs = content_type_qs.filter(model__in=model_names)

        for content_type in content_type_qs:
            redirect_model_class.objects.create(
                pattern=f'/zbs/{from_app}/{content_type.model}/',
                repl=f'/zbs/{to_app}/{content_type.model}/',
                start_date=localtime(),
                end_date=localtime() + datetime.timedelta(days=365),
            )

    return _create_redirects


def set_unique_values_for_string_field(  # noqa: CAC001
        app_label: str, model_name: str, field_name: str
) -> Callable:
    def _set_unique_values_for_string_field(
            apps: StateApps, schema: BaseDatabaseSchemaEditor
    ) -> None:
        model_class = apps.get_model(app_label, model_name)
        max_length = model_class._meta.get_field(field_name).max_length

        for item in (
                model_class.objects.filter(**{f'{field_name}__isnull': False}
                                           ).values(**{f'{field_name}__lower': Lower(field_name)}
                                                    ).annotate(**{f'{field_name}__count': Count(f'{field_name}__lower')}
                                                               ).filter(**{f'{field_name}__count__gt': 1}
                                                                        ).order_by(f'-{field_name}__count')
        ):
            num = 0
            for db_id, db_value in model_class.objects.filter(
                    **{f'{field_name}__iexact': item[f'{field_name}__lower']}
            ).values_list('pk', field_name)[1:]:
                while True:
                    num += 1
                    max_new_value_length = max_length - (len(str(num)) + 1)
                    new_value = f'{db_value[:max_new_value_length]}-{num}'
                    if not model_class.objects.filter(
                            **{f'{field_name}__iexact': new_value}
                    ).exists():
                        model_class.objects.filter(pk=db_id).update(**{field_name: new_value})
                        break

    return _set_unique_values_for_string_field


def generate_uuids_for_all_instances(app_label: str, model_name: str):
    def _generate_uuids_for_all_instances(
            apps: StateApps, schema: BaseDatabaseSchemaEditor
    ) -> None:
        model_class = apps.get_model(app_label, model_name)
        for item_id in model_class.objects.values_list('pk', flat=True).iterator():
            model_class.objects.filter(id=item_id).update(uuid=uuid.uuid4())

    return _generate_uuids_for_all_instances

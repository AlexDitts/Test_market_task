# Generated by Django 4.2.2 on 2023-08-23 11:27

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "is_admin",
                    models.BooleanField(
                        default=False,
                        help_text="Указывает, имеет ли пользователь статус администратора",
                        verbose_name="Пользователь может получить доступ к административной панели",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=False,
                        help_text="Указывает, активирована ли учетная запись пользователя",
                        verbose_name="Пользователь активен (не забанен)",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        help_text="Номер телефона",
                        max_length=12,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                "(\\+7|7|8)?[\\s\\-]?\\(?[489][0-9]{2}\\)?[\\s\\-]?[0-9]{3}[\\s\\-]?[0-9]{2}[\\s\\-]?[0-9]{2}"
                            )
                        ],
                        verbose_name="Номер телефона",
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True,
                        help_text="E-mail",
                        max_length=254,
                        null=True,
                        verbose_name="E-mail пользователя",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True,
                        help_text="Имя",
                        max_length=80,
                        null=True,
                        verbose_name="Имя пользователя",
                    ),
                ),
                (
                    "second_name",
                    models.CharField(
                        blank=True,
                        help_text="Отчество",
                        max_length=80,
                        null=True,
                        verbose_name="Отчество пользователя",
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True,
                        help_text="Фамилия",
                        max_length=80,
                        null=True,
                        verbose_name="Фамилия пользователя",
                    ),
                ),
                (
                    "birthdate",
                    models.DateField(
                        blank=True,
                        help_text="Дата рождения пользователя",
                        null=True,
                        verbose_name="Дата рождения",
                    ),
                ),
                (
                    "gender",
                    models.CharField(
                        choices=[("male", "Мужской"), ("female", "Женский")],
                        default="male",
                        help_text="Пол пользователя",
                        max_length=6,
                        verbose_name="Пол",
                    ),
                ),
                (
                    "city",
                    models.CharField(
                        blank=True,
                        help_text="Город проживания пользователя",
                        max_length=256,
                        null=True,
                        verbose_name="Город",
                    ),
                ),
                (
                    "street",
                    models.CharField(
                        blank=True,
                        help_text="Улица проживания пользователя",
                        max_length=256,
                        null=True,
                        verbose_name="Улица",
                    ),
                ),
                (
                    "house_number",
                    models.CharField(
                        blank=True,
                        help_text="Номер дома пользователя",
                        max_length=256,
                        null=True,
                        verbose_name="Дом",
                    ),
                ),
                (
                    "apartment_number",
                    models.CharField(
                        blank=True,
                        help_text="Номер квартиры | офиса пользователя",
                        max_length=256,
                        null=True,
                        verbose_name="Квартира",
                    ),
                ),
                (
                    "last_login",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Указывает, когда пользователь входил в систему в последний раз",
                        verbose_name="Время последнего входа в систему",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        help_text="Указывает, когда пользователь был зарегистрирован",
                        verbose_name="Дата регистрации пользователя",
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Группы, к которым принадлежит этот пользователь. Пользователь получитвсе разрешения предоставляется каждой из их групп.",
                        related_name="users",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="Группы",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "Пользователь",
                "verbose_name_plural": "Пользователи",
            },
        ),
        migrations.CreateModel(
            name="SMSKey",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("key", models.CharField(max_length=4)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sms_key",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
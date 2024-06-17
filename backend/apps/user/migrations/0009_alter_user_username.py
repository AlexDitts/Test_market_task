# Generated by Django 4.2.2 on 2024-02-02 14:29

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0008_alter_smskey_update_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="username",
            field=models.CharField(
                help_text="Номер телефона",
                max_length=13,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        "(\\+7|7|8)?[\\s\\-]?\\(?[489][0-9]{2}\\)?[\\s\\-]?[0-9]{3}[\\s\\-]?[0-9]{2}[\\s\\-]?[0-9]{2}"
                    )
                ],
                verbose_name="Номер телефона",
            ),
        ),
    ]
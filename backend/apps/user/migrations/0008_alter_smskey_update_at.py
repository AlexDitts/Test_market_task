# Generated by Django 4.2.2 on 2024-02-02 08:06

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0007_user_update_username"),
    ]

    operations = [
        migrations.AlterField(
            model_name="smskey",
            name="update_at",
            field=models.DateTimeField(
                auto_now_add=True, null=True, verbose_name="Дата последнего обновления"
            ),
        ),
    ]
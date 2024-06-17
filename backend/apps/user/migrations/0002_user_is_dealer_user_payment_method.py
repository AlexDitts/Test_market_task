# Generated by Django 4.2.2 on 2023-09-15 09:40

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_dealer",
            field=models.BooleanField(default=False, verbose_name="Является дилером"),
        ),
        migrations.AddField(
            model_name="user",
            name="payment_method",
            field=models.CharField(
                choices=[("prepaid", "Предоплата"), ("postpaid", "Постоплата")],
                default="prepaid",
                help_text="Выбирается из списка возможных вариантов оплаты",
                verbose_name="Способ оплаты",
            ),
        ),
    ]
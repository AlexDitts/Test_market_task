from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.credentials.models import SMSRuCredentials, EmailCredentials
from apps.credentials.utils import set_smsru_credentials, set_email_credentials


@receiver(post_save, sender=SMSRuCredentials)
def social_app_on_save(*args: tuple, **kwargs: dict) -> None:
	set_smsru_credentials()


@receiver(post_save, sender=EmailCredentials)
def social_app_on_save(*args: tuple, **kwargs: dict) -> None:
	set_email_credentials()

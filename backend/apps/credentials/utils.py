from contextlib import suppress

from django.apps import apps
from django.conf import settings
from django.db import ProgrammingError

from apps.credentials.models import SMSRuCredentials, EmailCredentials


def set_smsru_credentials() -> None:
	with suppress(LookupError, ProgrammingError):
		smsru_credentials: SMSRuCredentials = apps.get_model('credentials', 'smsrucredentials').get_solo()
		settings.SMS_RU = {
			"API_ID": smsru_credentials.api_id or settings.SMS_RU["API_ID"],
			"LOGIN": smsru_credentials.login or settings.SMS_RU["LOGIN"],
			"PASSWORD": smsru_credentials.password or settings.SMS_RU["PASSWORD"],
			"TEST": smsru_credentials.test or settings.SMS_RU["TEST"],
			"SENDER": smsru_credentials.sender or settings.SMS_RU["SENDER"],
		}


def set_email_credentials() -> None:
	with suppress(LookupError, ProgrammingError):
		email_credentials: EmailCredentials = apps.get_model('credentials', 'emailcredentials').get_solo()
		if not email_credentials.use_ssl and not email_credentials.use_tls:
			use_ssl, use_tls = settings.EMAIL_USE_SSL, settings.EMAIL_USE_TLS
		else:
			use_ssl, use_tls = (True, False) if email_credentials.use_ssl else (False, True)
		settings.EMAIL_HOST = email_credentials.host or settings.EMAIL_HOST
		settings.EMAIL_PORT = email_credentials.port or settings.EMAIL_PORT
		settings.EMAIL_USE_TLS = use_tls
		settings.EMAIL_USE_SSL = use_ssl
		settings.EMAIL_HOST_USER = email_credentials.host_user or settings.EMAIL_HOST_USER
		settings.EMAIL_HOST_PASSWORD = email_credentials.host_password or settings.EMAIL_HOST_PASSWORD
		settings.DEFAULT_FROM_EMAIL = email_credentials.default_from_email or settings.DEFAULT_FROM_EMAIL

from django.apps import AppConfig


class CredentialsConfig(AppConfig):
	default_auto_field = 'django.db.models.BigAutoField'
	name = 'apps.credentials'
	verbose_name = 'Интеграции'

	# def ready(self):
		# from . import signals

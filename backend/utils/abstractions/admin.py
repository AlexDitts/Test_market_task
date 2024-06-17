from django.contrib.admin import ModelAdmin, StackedInline
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Model
from solo.admin import SingletonModelAdmin


class AbstractAdmin(ModelAdmin):
	"""
	Base class from which all models should be inherited, in order
	 to have an option to add behavior to the group of admin models
	"""
	...


class AbstractSoloAdmin(SingletonModelAdmin):
	"""
	Base class from which all models should be inherited, in order
	 to have an option to add behavior to the group of admin models
	"""
	...


class AbstractStackedInline(StackedInline):
	"""
	Base class from which all models should be inherited, in order
	 to have an option to add behavior to the group of admin models
	"""
	...


class ReadOnlyStackedInline(AbstractStackedInline):
	"""
	Base class from which all models should be inherited, in order
	 to have an option to add behavior to the group of admin models
	"""

	def has_change_permission(self, request: WSGIRequest, obj: Model = None) -> bool:
		return False

	def has_add_permission(self, request: WSGIRequest, obj: Model = None) -> bool:
		return False

	def has_delete_permission(self, request: WSGIRequest, obj: Model = None) -> bool:
		return False

from rest_framework import permissions


class UserPermission(permissions.BasePermission):

	def has_permission(self, request, view):
		if view.action == 'list':
			return request.user.is_authenticated and request.user.is_admin
		elif view.action == 'create':
			return False
		elif view.action in ['retrieve', 'update', 'partial_update', 'destroy']:
			return True
		else:
			return True

	def has_object_permission(self, request, view, obj):
		if not request.user.is_authenticated:
			return False
		if view.action == 'retrieve':
			return obj == request.user or request.user.is_admin
		elif view.action in ['update', 'partial_update']:
			return obj == request.user or request.user.is_admin
		elif view.action == 'destroy':
			return request.user.is_admin
		else:
			return True

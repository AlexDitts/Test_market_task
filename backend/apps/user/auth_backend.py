from django.contrib.auth.backends import ModelBackend
from apps.user.models import User


class PasswordlessAuthBackend(ModelBackend):
    """
    Log in to Django without providing a password.
    """

    def authenticate(self, username: str | None = None, **kwargs: dict) -> User | None:
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    def get_user(self, user_id: int) -> User | None:
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
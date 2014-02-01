from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from app.api import authenticate


class UserBackend(ModelBackend):
    def authenticate(self, request, username, password):
        if not username or not password:
            return

        token = authenticate(username, password)

        if token:
            user, created = User.objects.get_or_create(username=username)
            user.token = token

        return user

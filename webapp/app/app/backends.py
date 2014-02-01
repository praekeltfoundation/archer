from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from app.api import authenticate


class UserBackend(ModelBackend):
    def authenticate(self, request, username, password):
        if not username or not password:
            return

        user_data = authenticate(username, password)

        if user_data['user_id']:
            user, created = User.objects.get_or_create(username=username)
            user.token = user_data['user_id']
            return user

import requests
import json
from django.conf import settings


class InvalidResponse(Exception):
    pass


def register(user):
    response = requests.put(settings.USER_SERVICE_URL, user)

    if response.status_code == 200:
        return json.loads(response.text)

    raise InvalidResponse(response.text)

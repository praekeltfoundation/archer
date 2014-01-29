import requests
import json
from django.conf import settings


class InvalidResponse(Exception):
    pass


def register(user):
    response = requests.put(settings.NEO4J_URL, user)

    if response.status_code == 200:
        return json.loads(response.text)

    raise InvalidResponse(response.text)

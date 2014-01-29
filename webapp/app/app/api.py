import requests
import json
from django.conf import settings


class InvalidResponse(Exception):
    pass


def register(user):
    response = requests.put(settings.USER_SERVICE_URL, json.dumps(user))

    if response.status_code == 200:
        return json.loads(response.text)

    raise InvalidResponse(response.text)


def authenticate(username, password):
    import uuid
    return str(uuid.uuid4())

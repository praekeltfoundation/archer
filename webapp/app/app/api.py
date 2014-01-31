import requests
import json
from django.conf import settings


class InvalidResponse(Exception):
    pass


def register(user):
    response = requests.put(settings.USER_SERVICE_URL, json.dumps(user))

    if not response.status_code == 200:
        raise InvalidResponse(response.text)

    return response


def authenticate(username, password):
    '''
    Expects authentication toke back
    '''
    data = {
        'username': username,
        'password': password
    }
    response = requests.post(settings.USER_SERVICE_URL, json.dumps(data))

    if not response.status_code == 200:
        raise InvalidResponse(response.text)

    return response.text

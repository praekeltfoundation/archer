import requests
from django.conf import settings


class InvalidResponse(Exception):
    pass


def register(user):
    return requests.put(settings.NEO4J_URL, user)

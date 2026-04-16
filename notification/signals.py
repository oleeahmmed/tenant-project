from django.apps import apps

from .integrations import connect_optional_integrations


def _connect():
    connect_optional_integrations()


_connect()

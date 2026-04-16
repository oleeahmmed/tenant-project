"""
Wire signals from optional apps. Safe when chat / jiraclone are absent from INSTALLED_APPS.
"""

from django.apps import apps as django_apps


def connect_optional_integrations() -> None:
    if django_apps.is_installed("chat"):
        from . import chat as chat_hooks

        chat_hooks.connect()

    if django_apps.is_installed("jiraclone"):
        from . import jiraclone as jira_hooks

        jira_hooks.connect()

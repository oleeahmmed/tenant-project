"""
Config App Configuration
"""
from django.apps import AppConfig


class ConfigConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'config'
    verbose_name = 'Configuration'
    
    def ready(self):
        """Import admin when app is ready"""
        try:
            import config.admin  # noqa
        except ImportError:
            pass

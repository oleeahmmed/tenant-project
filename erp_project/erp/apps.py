from django.apps import AppConfig


class ErpConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'erp'
    
    def ready(self):
        # Import signals to register them
        import erp.signals  # noqa: F401

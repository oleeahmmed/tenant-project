from django.apps import apps

from auth_tenants.models import Permission


MODULE_TO_APP_LABELS = {
    "foundation": ["foundation"],
    "inventory": ["inventory"],
    "finance": ["finance"],
    "purchase": ["purchase"],
    "sales": ["sales"],
    "production": ["production"],
    "hrm": ["hrm"],
    "recruitment": ["recruitment"],
    "payroll": ["payroll"],
    "auth_tenants": ["auth_tenants"],
}

CRUD_ACTIONS = ("view", "add", "change", "delete")
MODULE_BASE_ACTIONS = (
    ("view", "View module"),
    ("manage", "Manage module"),
    ("delete", "Delete records"),
)


def sync_default_model_permissions(module_codes):
    """
    Ensure Permission catalog contains default Django CRUD-like rows
    for all models inside selected modules.
    Codename format: app.model.action (example: foundation.product.view)
    """
    selected = {(x or "").strip().lower() for x in (module_codes or [])}
    for module in selected:
        # Coarse-grained app permissions used by mixins/routes.
        for action, label_prefix in MODULE_BASE_ACTIONS:
            Permission.objects.get_or_create(
                codename=f"{module}.{action}",
                defaults={
                    "label": f"{label_prefix} ({module.title()})",
                    "category": module if module in dict(Permission.CATEGORIES) else "system",
                    "is_active": True,
                },
            )

        app_labels = MODULE_TO_APP_LABELS.get(module, [])
        for app_label in app_labels:
            cfg = apps.get_app_config(app_label)
            for model in cfg.get_models():
                model_name = model._meta.model_name
                verbose = model._meta.verbose_name.title()
                for action in CRUD_ACTIONS:
                    codename = f"{app_label}.{model_name}.{action}"
                    label = f"{action.title()} {verbose}"
                    Permission.objects.get_or_create(
                        codename=codename,
                        defaults={
                            "label": label,
                            "category": module if module in dict(Permission.CATEGORIES) else "system",
                            "is_active": True,
                        },
                    )


"""Who can be assigned to issues in a project (tenant users from department mappings)."""

from django.contrib.auth import get_user_model

User = get_user_model()


def assignable_users_for_project(project):
    """
    Assignment source is project department user mappings only.
    If no users are mapped in departments, return no users.
    """
    tenant = project.tenant
    base = User.objects.filter(tenant=tenant, is_active=True).order_by("name")
    department_links = list(project.department_assignments.prefetch_related("users"))
    ids = set()
    for link in department_links:
        for user in link.users.all():
            ids.add(user.id)
    if not ids:
        return User.objects.none()
    return base.filter(pk__in=ids)

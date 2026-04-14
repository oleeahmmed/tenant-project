"""Who can be assigned to issues in a project (union of all project teams)."""

from django.contrib.auth import get_user_model

User = get_user_model()


def assignable_users_for_project(project):
    """
    If the project has no teams, all tenant users are assignable (backward compatible).
    If teams exist, only users who belong to at least one team are assignable.
    """
    tenant = project.tenant
    base = User.objects.filter(tenant=tenant, is_active=True).order_by("name")
    teams = list(project.teams.all())
    department_links = list(project.department_assignments.prefetch_related("employees__user"))
    if not teams and not department_links:
        return base
    ids = set()
    for team in teams:
        ids.update(team.members.values_list("pk", flat=True))
    for link in department_links:
        for emp in link.employees.all():
            if emp.user_id:
                ids.add(emp.user_id)
    if not ids:
        return User.objects.none()
    return base.filter(pk__in=ids)

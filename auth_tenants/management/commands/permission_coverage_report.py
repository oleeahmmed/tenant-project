from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand
from django.urls import URLPattern, URLResolver, get_resolver


TARGET_APPS = {
    "foundation",
    "inventory",
    "hrm",
    "recruitment",
    "finance",
    "purchase",
    "sales",
    "production",
    "auth_tenants",
}


def _walk_patterns(patterns, prefix=""):
    for p in patterns:
        route = f"{prefix}{p.pattern}"
        if isinstance(p, URLResolver):
            yield from _walk_patterns(p.url_patterns, route)
        elif isinstance(p, URLPattern):
            yield route, p


def _infer_permissions(view_cls):
    if not view_cls:
        return []
    perm = getattr(view_cls, "permission_codename", "") or ""
    if perm:
        return [perm]
    out = []
    for attr in ("permission_codename_read", "permission_codename_write", "permission_codename_delete"):
        v = getattr(view_cls, attr, "") or ""
        if v:
            out.append(v)
    return out


class Command(BaseCommand):
    help = "Generate app-wise permission coverage report from URL routes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="docs/permission_coverage_report.md",
            help="Output markdown file path.",
        )

    def handle(self, *args, **options):
        resolver = get_resolver()
        rows_by_app = defaultdict(list)

        for route, pattern in _walk_patterns(resolver.url_patterns):
            callback = pattern.callback
            view_cls = getattr(callback, "view_class", None)
            module = ""
            if view_cls:
                module = (getattr(view_cls, "__module__", "") or "").split(".", 1)[0]
            else:
                module = (getattr(callback, "__module__", "") or "").split(".", 1)[0]
            if module not in TARGET_APPS:
                continue

            perms = _infer_permissions(view_cls)
            rows_by_app[module].append(
                {
                    "route": f"/{route}".replace("//", "/"),
                    "name": pattern.name or "",
                    "view": view_cls.__name__ if view_cls else getattr(callback, "__name__", "function"),
                    "permissions": ", ".join(sorted(set(perms))) if perms else "(mixin default/fallback)",
                }
            )

        lines = [
            "# Permission Coverage Report",
            "",
            "Auto-generated from Django URL resolver.",
            "",
        ]
        for app in sorted(rows_by_app.keys()):
            lines.append(f"## {app}")
            lines.append("")
            lines.append("| Route | URL Name | View | Permission Contract |")
            lines.append("|---|---|---|---|")
            for row in sorted(rows_by_app[app], key=lambda x: x["route"]):
                lines.append(
                    f"| `{row['route']}` | `{row['name']}` | `{row['view']}` | `{row['permissions']}` |"
                )
            lines.append("")

        output_path = Path(options["output"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Permission coverage report generated: {output_path}"))


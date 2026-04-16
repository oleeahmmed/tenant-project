"""
Core notification API — no imports from chat, jiraclone, or other feature apps.
"""

from __future__ import annotations

from typing import Iterable

from django.db import transaction

from .models import Notification


def notify_users(
    *,
    tenant_id: int,
    recipient_ids: Iterable[int],
    title: str,
    body: str = "",
    kind: str = "system.generic",
    link_url: str = "",
    metadata: dict | None = None,
    actor_id: int | None = None,
) -> int:
    """
    Create one Notification row per recipient. Returns number of rows created.
    """
    meta = metadata if metadata is not None else {}
    ids = [int(x) for x in recipient_ids if x]
    if not ids:
        return 0
    rows = [
        Notification(
            tenant_id=tenant_id,
            recipient_id=uid,
            title=title[:255],
            body=body or "",
            kind=kind[:64],
            link_url=(link_url or "")[:1024],
            metadata=meta,
            actor_id=actor_id,
        )
        for uid in set(ids)
    ]
    with transaction.atomic():
        Notification.objects.bulk_create(rows)
    return len(rows)


def unread_count_for_user(*, tenant_id: int | None, user_id: int) -> int:
    if tenant_id is None:
        return 0
    return Notification.objects.filter(
        tenant_id=tenant_id,
        recipient_id=user_id,
        read_at__isnull=True,
    ).count()

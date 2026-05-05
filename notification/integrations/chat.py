"""
Chat → notifications (no Django signals).

Called from ``chat.models.ChatMessage.save()`` via ``transaction.on_commit`` when
the ``notification`` app is installed.
"""

from __future__ import annotations

import logging

from django.urls import reverse

logger = logging.getLogger(__name__)


def notify_new_chat_message(message_id: int) -> None:
    """Notify room members (except sender) when a new message exists."""
    from chat.models import ChatMember, ChatMessage

    try:
        instance = ChatMessage.objects.select_related("room", "sender").get(pk=message_id)
    except ChatMessage.DoesNotExist:
        return

    from notification.services import notify_users

    room = instance.room
    tenant_id = room.tenant_id
    sender_id = instance.sender_id

    member_ids = list(
        ChatMember.objects.filter(room_id=room.pk).exclude(user_id=sender_id).values_list(
            "user_id", flat=True
        )
    )
    if not member_ids:
        return

    preview = (instance.body or "").strip()
    if not preview:
        preview = "[Media or attachment]"
    if len(preview) > 240:
        preview = preview[:237] + "…"

    sender_name = getattr(instance.sender, "name", None) or getattr(instance.sender, "email", "Someone")
    title = f"New message from {sender_name}"
    link = f"{reverse('chat:chat_app')}?room={room.pk}"
    meta = {
        "source": "chat",
        "room_id": room.pk,
        "message_id": instance.pk,
    }

    try:
        notify_users(
            tenant_id=tenant_id,
            recipient_ids=member_ids,
            title=title,
            body=preview,
            kind="chat.message",
            link_url=link,
            metadata=meta,
            actor_id=sender_id,
        )
    except Exception:
        logger.exception("notification: chat message hook failed")

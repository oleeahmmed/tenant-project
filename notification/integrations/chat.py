"""
Chat → notifications. Loaded only if ``chat`` is installed.
"""

import logging

from django.db.models.signals import post_save
from django.urls import reverse

logger = logging.getLogger(__name__)


def connect() -> None:
    from chat.models import ChatMessage

    post_save.connect(
        _on_chat_message,
        sender=ChatMessage,
        dispatch_uid="notification_chat_post_save",
    )


def _on_chat_message(sender, instance, created, **kwargs):
    if not created:
        return

    from chat.models import ChatMember

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

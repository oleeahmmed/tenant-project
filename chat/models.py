from django.conf import settings
from django.db import models


class ChatRoom(models.Model):
    class Kind(models.TextChoices):
        DIRECT = "direct", "Direct"
        GROUP = "group", "Group"

    tenant = models.ForeignKey(
        "auth_tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="chat_rooms",
    )
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.DIRECT)
    title = models.CharField(max_length=255, blank=True)
    direct_key = models.CharField(max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat_rooms_created",
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "direct_key"],
                condition=models.Q(kind="direct") & ~models.Q(direct_key=""),
                name="chatroom_unique_direct_per_tenant",
            ),
        ]

    def __str__(self):
        if self.kind == self.Kind.GROUP:
            return self.title or f"Group #{self.pk}"
        return f"Direct {self.direct_key}"

    def display_title(self, for_user):
        if self.kind == self.Kind.GROUP:
            return self.title or "Group"
        other = self.members.exclude(user_id=for_user.pk).select_related("user").first()
        if other:
            return other.user.name
        return "Chat"


class ChatMember(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_memberships")
    joined_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)

    class Meta:
        unique_together = [("room", "user")]


class ChatMessage(models.Model):
    class MessageType(models.TextChoices):
        TEXT = "text", "Text"
        IMAGE = "image", "Image"
        FILE = "file", "File"
        VOICE = "voice", "Voice"

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_messages_sent")
    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT,
    )
    body = models.TextField(blank=True)
    image = models.ImageField(upload_to="chat/images/", blank=True, null=True)
    file = models.FileField(upload_to="chat/files/", blank=True, null=True)
    voice = models.FileField(upload_to="chat/voice/", blank=True, null=True)
    file_display_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.room_id} · {self.message_type} · {self.created_at}"

    def preview_line(self, max_len: int = 56) -> str:
        t = self.message_type
        if t == self.MessageType.TEXT:
            s = (self.body or "").strip().replace("\n", " ")
            if len(s) > max_len:
                return s[: max_len - 1] + "…"
            return s
        if t == self.MessageType.IMAGE:
            cap = (self.body or "").strip()
            return ("📷 " + cap) if cap else "📷 Photo"
        if t == self.MessageType.FILE:
            return "📎 " + (self.file_display_name or "File")
        if t == self.MessageType.VOICE:
            return "🎤 Voice message"
        return "Message"

    def sidebar_preview(self, for_user) -> str:
        line = self.preview_line()
        if self.sender_id == getattr(for_user, "pk", None):
            return f"You: {line}" if line else "You: Tap to continue"
        first = ""
        if self.sender:
            parts = (self.sender.name or "").split()
            first = parts[0] if parts else "?"
        return f"{first}: {line}" if line else f"{first}: sent a message"

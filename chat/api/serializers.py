from rest_framework import serializers

from auth_tenants.models import User
from chat.models import ChatMessage, ChatRoom


class ChatRoomSerializer(serializers.ModelSerializer):
    display_title = serializers.SerializerMethodField()
    member_ids = serializers.SerializerMethodField()
    last_message_at = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = [
            "id",
            "kind",
            "title",
            "display_title",
            "member_ids",
            "last_message_at",
            "unread_count",
            "created_at",
        ]

    def get_display_title(self, obj):
        user = self.context.get("user")
        if user:
            return obj.display_title(user)
        return obj.title or "Chat"

    def get_member_ids(self, obj):
        return list(obj.members.values_list("user_id", flat=True))

    def get_last_message_at(self, obj):
        row = obj.messages.order_by("-created_at").values_list("created_at", flat=True).first()
        return row.isoformat() if row else None

    def get_unread_count(self, obj):
        # Uses pre-annotated value from queryset when available.
        val = getattr(obj, "unread_count", None)
        try:
            return int(val or 0)
        except (TypeError, ValueError):
            return 0


class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    voice_url = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "room_id",
            "sender_id",
            "sender_name",
            "message_type",
            "body",
            "file_display_name",
            "image_url",
            "file_url",
            "voice_url",
            "created_at",
        ]

    def get_sender_name(self, obj):
        return getattr(obj.sender, "name", "") or getattr(obj.sender, "email", "")

    def _abs(self, path):
        req = self.context.get("request")
        if not path:
            return None
        return req.build_absolute_uri(path) if req else path

    def get_image_url(self, obj):
        return self._abs(obj.image.url) if obj.image else None

    def get_file_url(self, obj):
        return self._abs(obj.file.url) if obj.file else None

    def get_voice_url(self, obj):
        return self._abs(obj.voice.url) if obj.voice else None


class ChatDirectStartSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

    def validate_user_id(self, value):
        tenant = self.context["tenant"]
        request = self.context["request"]
        if value == request.user.pk:
            raise serializers.ValidationError("Cannot start direct chat with yourself.")
        if not User.objects.filter(pk=value, tenant=tenant, is_active=True).exists():
            raise serializers.ValidationError("Invalid user for tenant.")
        return value


class ChatGroupCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
    )

    def validate_member_ids(self, value):
        tenant = self.context["tenant"]
        valid_ids = set(User.objects.filter(tenant=tenant, is_active=True).values_list("id", flat=True))
        cleaned = []
        for uid in value:
            if uid in valid_ids:
                cleaned.append(uid)
        if not cleaned:
            raise serializers.ValidationError("No valid members selected.")
        return cleaned


class ChatUserOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email"]


class ChatRoomUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)

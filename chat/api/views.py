from django.db.models import Count, Max, Q
from django.shortcuts import get_object_or_404
from rest_framework import status

from auth_tenants.permissions import TenantAPIView
from auth_tenants.models import User
from chat.broadcast import broadcast_room_message
from chat.forms import ChatMessageForm
from chat.models import ChatMember, ChatMessage, ChatRoom
from chat.services import create_group_room, get_or_create_direct_room
from chat.views import _create_message_with_image_fallback, _looks_like_raster_image, _message_payload, _upload_basename, _upload_ct, _upload_ext

from .serializers import (
    ChatDirectStartSerializer,
    ChatGroupCreateSerializer,
    ChatMessageSerializer,
    ChatRoomSerializer,
    ChatRoomUpdateSerializer,
    ChatUserOptionSerializer,
)


class ChatApiBase(TenantAPIView):
    module_code = "chat"
    required_permission = "chat.view"

    def get_room_or_404(self, tenant, room_id):
        room = get_object_or_404(ChatRoom, pk=room_id, tenant=tenant)
        if not ChatMember.objects.filter(room=room, user_id=self.request.user.pk).exists():
            self.permission_denied(self.request, message="Room not found.")
        return room


class ChatRoomListView(ChatApiBase):
    def get(self, request):
        tenant = self.get_tenant()
        qs = (
            ChatRoom.objects.filter(tenant=tenant, members__user=request.user)
            .annotate(
                last_at=Max("messages__created_at"),
                unread_count=Count("messages", filter=~Q(messages__sender=request.user)),
            )
            .distinct()
            .order_by("-last_at", "-pk")
        )
        return self.success_response(ChatRoomSerializer(qs, many=True, context={"user": request.user}).data)


class ChatUserListView(ChatApiBase):
    required_permission = "chat.manage"

    def get(self, request):
        tenant = self.get_tenant()
        rows = (
            User.objects.filter(tenant=tenant, is_active=True)
            .exclude(pk=request.user.pk)
            .order_by("name", "email")
        )
        return self.success_response(ChatUserOptionSerializer(rows, many=True).data)


class ChatDirectStartView(ChatApiBase):
    required_permission = "chat.manage"

    def post(self, request):
        tenant = self.get_tenant()
        serializer = ChatDirectStartSerializer(data=request.data, context={"tenant": tenant, "request": request})
        serializer.is_valid(raise_exception=True)
        other = get_object_or_404(User, pk=serializer.validated_data["user_id"], tenant=tenant, is_active=True)
        room, created = get_or_create_direct_room(tenant, request.user, other)
        return self.success_response(ChatRoomSerializer(room, context={"user": request.user}).data, created=created, code=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class ChatGroupCreateView(ChatApiBase):
    required_permission = "chat.manage"

    def post(self, request):
        tenant = self.get_tenant()
        serializer = ChatGroupCreateSerializer(data=request.data, context={"tenant": tenant})
        serializer.is_valid(raise_exception=True)
        room = create_group_room(
            tenant,
            request.user,
            serializer.validated_data["title"],
            serializer.validated_data["member_ids"],
        )
        return self.success_response(ChatRoomSerializer(room, context={"user": request.user}).data, code=status.HTTP_201_CREATED)


class ChatMessageListView(ChatApiBase):
    def get(self, request, room_id: int):
        tenant = self.get_tenant()
        room = self.get_room_or_404(tenant, room_id)
        try:
            limit = min(max(int(request.GET.get("limit", 50)), 1), 200)
        except (TypeError, ValueError):
            limit = 50
        qs = ChatMessage.objects.filter(room=room).select_related("sender").order_by("-created_at")[:limit]
        rows = list(reversed(qs))
        return self.success_response(ChatMessageSerializer(rows, many=True, context={"request": request}).data)


class ChatRoomDetailView(ChatApiBase):
    def get(self, request, room_id: int):
        tenant = self.get_tenant()
        room = self.get_room_or_404(tenant, room_id)
        payload = ChatRoomSerializer(room, context={"user": request.user}).data
        members = (
            room.members.select_related("user")
            .order_by("-is_admin", "user__name", "user__email")
            .values("user_id", "is_admin", "user__name", "user__email")
        )
        payload["members"] = [
            {
                "id": row["user_id"],
                "name": row["user__name"] or row["user__email"] or f"User {row['user_id']}",
                "email": row["user__email"] or "",
                "is_admin": bool(row["is_admin"]),
            }
            for row in members
        ]
        return self.success_response(payload)

    def patch(self, request, room_id: int):
        tenant = self.get_tenant()
        room = self.get_room_or_404(tenant, room_id)
        if room.kind != ChatRoom.Kind.GROUP:
            return self.error_response("Only group rooms can be updated.", status.HTTP_400_BAD_REQUEST)
        membership = ChatMember.objects.filter(room=room, user=request.user).first()
        if request.user.role != "super_admin" and (membership is None or not membership.is_admin):
            return self.error_response("Only group admins can update group settings.", status.HTTP_403_FORBIDDEN)
        serializer = ChatRoomUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        room.title = serializer.validated_data["title"].strip()[:255]
        room.save(update_fields=["title"])
        return self.success_response(ChatRoomSerializer(room, context={"user": request.user}).data)


class ChatMessageCreateView(ChatApiBase):
    required_permission = "chat.manage"

    def post(self, request, room_id: int):
        tenant = self.get_tenant()
        room = self.get_room_or_404(tenant, room_id)
        form = ChatMessageForm(request.data, request.FILES)
        if not form.is_valid():
            return self.error_response("validation_failed", status.HTTP_400_BAD_REQUEST, errors=form.errors.get_json_data())

        body = (form.cleaned_data.get("body") or "").strip()
        image = form.cleaned_data.get("image")
        file = form.cleaned_data.get("file")
        voice = form.cleaned_data.get("voice")

        msg_type = ChatMessage.MessageType.TEXT
        save_image = None
        save_file = None
        save_voice = None
        display = ""

        if voice:
            msg_type = ChatMessage.MessageType.VOICE
            save_voice = voice
        elif image:
            ct = _upload_ct(image)
            ext = _upload_ext(image)
            if ct == "image/svg+xml" or ext == "svg":
                msg_type = ChatMessage.MessageType.FILE
                save_file = image
                display = (_upload_basename(image) or "")[:255]
            elif _looks_like_raster_image(image):
                msg_type = ChatMessage.MessageType.IMAGE
                save_image = image
            else:
                msg_type = ChatMessage.MessageType.FILE
                save_file = image
                display = (_upload_basename(image) or "")[:255]
        elif file:
            msg_type = ChatMessage.MessageType.FILE
            save_file = file
            display = (_upload_basename(file) or "")[:255]

        if not body and not save_image and not save_file and not save_voice:
            return self.error_response("empty", status.HTTP_400_BAD_REQUEST)

        if not display and save_file:
            display = (_upload_basename(save_file) or "")[:255]

        if msg_type == ChatMessage.MessageType.IMAGE and save_image:
            msg = _create_message_with_image_fallback(
                room=room,
                sender=request.user,
                message_type=msg_type,
                body=body,
                save_image=save_image,
                save_file=None,
                save_voice=save_voice,
                display=display,
            )
        else:
            msg = ChatMessage.objects.create(
                room=room,
                sender=request.user,
                message_type=msg_type,
                body=body,
                image=save_image,
                file=save_file,
                voice=save_voice,
                file_display_name=display[:255],
            )

        ws_payload = {"event": "new_message", "message": _message_payload(request, msg)}
        broadcast_room_message(room.pk, ws_payload)
        return self.success_response(ChatMessageSerializer(msg, context={"request": request}).data, code=status.HTTP_201_CREATED)

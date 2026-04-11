import json

from django.contrib import messages
from django.db.models import Max
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from auth_tenants.models import User
from hrm.tenant_scope import user_belongs_to_workspace_tenant

from .broadcast import broadcast_room_message
from .forms import ChatMessageForm, GroupChatForm
from .mixins import ChatDashboardAccessMixin, ChatPageContextMixin
from .models import ChatMember, ChatMessage, ChatRoom
from .services import create_group_room, get_or_create_direct_room


def _last_messages_for_rooms(room_ids: list) -> dict:
    if not room_ids:
        return {}
    last_by = {}
    for msg in (
        ChatMessage.objects.filter(room_id__in=room_ids)
        .select_related("sender")
        .order_by("room_id", "-created_at")
    ):
        if msg.room_id not in last_by:
            last_by[msg.room_id] = msg
    return last_by


def _tenant_users_queryset(request):
    t = getattr(request, "hrm_tenant", None)
    if t is None:
        return User.objects.none()
    return (
        User.objects.filter(tenant=t, is_active=True)
        .exclude(pk=request.user.pk)
        .order_by("name")
    )


def _room_for_user(request, room_id: int) -> ChatRoom:
    t = getattr(request, "hrm_tenant", None)
    if t is None:
        raise Http404("No tenant")
    room = get_object_or_404(ChatRoom, pk=room_id, tenant=t)
    if not ChatMember.objects.filter(room=room, user_id=request.user.pk).exists():
        raise Http404("Room not found")
    return room


class ChatAppView(ChatDashboardAccessMixin, TemplateView):
    template_name = "chat/whatsapp.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        request = self.request
        t = getattr(request, "hrm_tenant", None)
        ctx["workspace_tenant"] = t
        ctx["room_id"] = None
        ctx["rooms"] = []
        ctx["chat_messages"] = []
        ctx["active_room"] = None
        ctx["tenant_users"] = _tenant_users_queryset(request)
        ctx["group_form"] = GroupChatForm(tenant_users_queryset=_tenant_users_queryset(request))
        ctx["message_form"] = ChatMessageForm()
        ctx["chat_json"] = "{}"
        ctx["show_group_modal"] = request.GET.get("new") == "group"

        if t is None:
            return ctx

        rooms_qs = (
            ChatRoom.objects.filter(tenant=t, members__user=request.user)
            .annotate(last_at=Max("messages__created_at"))
            .distinct()
            .order_by("-last_at", "-pk")
        )
        rooms_list = list(rooms_qs)
        last_map = _last_messages_for_rooms([r.pk for r in rooms_list])
        for r in rooms_list:
            r.last_msg = last_map.get(r.pk)
        ctx["rooms"] = rooms_list

        rid = request.GET.get("room")
        active = None
        if rid:
            try:
                active = _room_for_user(request, int(rid))
            except (ValueError, Http404):
                active = None
        if active is None and rooms_list:
            active = rooms_list[0]
        if active:
            ctx["room_id"] = active.pk
            ctx["active_room"] = active
            ctx["chat_messages"] = (
                ChatMessage.objects.filter(room=active)
                .select_related("sender")
                .order_by("created_at")[:200]
            )
            ws_scheme = "wss" if request.is_secure() else "ws"
            host = request.get_host()
            payload = {
                "roomId": active.pk,
                "displayTitle": active.display_title(request.user),
                "sendUrl": request.build_absolute_uri(
                    reverse("chat:send_message", kwargs={"room_id": active.pk})
                ),
                "wsUrl": f"{ws_scheme}://{host}/ws/chat/{active.pk}/",
            }
            ctx["chat_json"] = json.dumps(payload)
        return ctx


class StartDirectView(ChatDashboardAccessMixin, View):
    def post(self, request, *args, **kwargs):
        t = getattr(request, "hrm_tenant", None)
        if t is None:
            messages.error(request, "Select a workspace tenant first.")
            return redirect("chat:chat_app")
        try:
            other_id = int(request.POST.get("user_id", "0"))
        except (TypeError, ValueError):
            messages.error(request, "Invalid user.")
            return redirect("chat:chat_app")
        other = get_object_or_404(User, pk=other_id, tenant=t, is_active=True)
        if other.pk == request.user.pk:
            messages.error(request, "Pick someone else.")
            return redirect("chat:chat_app")
        if not user_belongs_to_workspace_tenant(request.user, t):
            raise Http404()
        room, _ = get_or_create_direct_room(t, request.user, other)
        return redirect(f"{reverse('chat:chat_app')}?room={room.pk}")


class GroupCreateView(ChatDashboardAccessMixin, View):
    def post(self, request, *args, **kwargs):
        t = getattr(request, "hrm_tenant", None)
        if t is None:
            messages.error(request, "No tenant.")
            return redirect("chat:chat_app")
        form = GroupChatForm(request.POST, tenant_users_queryset=_tenant_users_queryset(request))
        if not form.is_valid():
            messages.error(request, "Check the group name and members.")
            return redirect("chat:chat_app")
        title = form.cleaned_data["title"]
        members = list(form.cleaned_data["members"])
        ids = [u.pk for u in members if u.pk != request.user.pk]
        room = create_group_room(t, request.user, title, ids)
        messages.success(request, "Group created.")
        return redirect(f"{reverse('chat:chat_app')}?room={room.pk}")


class PostMessageView(ChatDashboardAccessMixin, View):
    def post(self, request, room_id, *args, **kwargs):
        room = _room_for_user(request, room_id)
        form = ChatMessageForm(request.POST, request.FILES)
        if not form.is_valid():
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {
                        "ok": False,
                        "error": "validation_failed",
                        "errors": form.errors.get_json_data(),
                    },
                    status=400,
                )
            messages.error(request, "Could not send.")
            return redirect(f"{reverse('chat:chat_app')}?room={room.pk}")

        body = (form.cleaned_data.get("body") or "").strip()
        image = form.cleaned_data.get("image")
        file = form.cleaned_data.get("file")
        voice = form.cleaned_data.get("voice")

        def _ctype(f):
            if f is None:
                return ""
            return (getattr(f, "content_type", None) or "").lower()

        msg_type = ChatMessage.MessageType.TEXT
        save_image = None
        save_file = None
        save_voice = None
        display = ""

        if voice:
            msg_type = ChatMessage.MessageType.VOICE
            save_voice = voice
        elif image:
            ct = _ctype(image)
            if ct.startswith("image/") or (getattr(image, "name", "") or "").lower().rsplit(".", 1)[-1] in (
                "jpg",
                "jpeg",
                "png",
                "gif",
                "webp",
                "bmp",
            ):
                msg_type = ChatMessage.MessageType.IMAGE
                save_image = image
            else:
                msg_type = ChatMessage.MessageType.FILE
                save_file = image
                display = (getattr(image, "name", "") or "")[:255]
        elif file:
            msg_type = ChatMessage.MessageType.FILE
            save_file = file
            display = (getattr(file, "name", "") or "")[:255]

        if not body and not save_image and not save_file and not save_voice:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "error": "empty"}, status=400)
            return redirect(f"{reverse('chat:chat_app')}?room={room.pk}")

        if not display and save_file:
            display = (getattr(save_file, "name", "") or "")[:255]

        try:
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
        except Exception:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse(
                    {"ok": False, "error": "Could not save this attachment. Try another file or format."},
                    status=400,
                )
            messages.error(request, "Could not save attachment.")
            return redirect(f"{reverse('chat:chat_app')}?room={room.pk}")

        ws_payload = {
            "event": "new_message",
            "message": {
                "id": msg.pk,
                "type": str(msg.message_type),
                "body": msg.body,
                "sender": request.user.name,
                "sender_id": request.user.pk,
                "created": msg.created_at.isoformat(),
                "image_url": request.build_absolute_uri(msg.image.url) if msg.image else None,
                "file_url": request.build_absolute_uri(msg.file.url) if msg.file else None,
                "file_name": msg.file_display_name or (msg.file.name if msg.file else ""),
                "voice_url": request.build_absolute_uri(msg.voice.url) if msg.voice else None,
            },
        }
        broadcast_room_message(room.pk, ws_payload)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": True, **ws_payload})
        return redirect(f"{reverse('chat:chat_app')}?room={room.pk}")

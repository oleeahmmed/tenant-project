import json
import logging

from django.contrib import messages
from django.conf import settings
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

logger = logging.getLogger(__name__)


def _upload_basename(upload) -> str:
    return (getattr(upload, "name", "") or "").split("/")[-1].split("\\")[-1]


def _upload_ext(upload) -> str:
    name = (_upload_basename(upload) or "").lower()
    if "." not in name:
        return ""
    return name.rsplit(".", 1)[-1]


def _upload_ct(upload) -> str:
    if upload is None:
        return ""
    return (getattr(upload, "content_type", None) or "").lower()


def _looks_like_raster_image(upload) -> bool:
    """
    Browsers often send camera/gallery files as application/octet-stream or with no extension.
    ImageField still needs a raster Pillow can open (HEIC may fail — handled via save fallback).
    """
    if upload is None:
        return False
    ct = _upload_ct(upload)
    ext = _upload_ext(upload)
    if ct == "image/svg+xml" or ext == "svg":
        return False
    if ct.startswith("image/"):
        return True
    if ext in ("jpg", "jpeg", "png", "gif", "webp", "bmp", "tif", "tiff", "jfif", "heic", "heif"):
        return True
    if ct not in ("application/octet-stream", "binary/octet-stream", ""):
        return False
    try:
        from io import BytesIO

        from PIL import Image as PILImage

        upload.seek(0)
        head = upload.read(512 * 1024)
        upload.seek(0)
        if not head:
            return False
        im = PILImage.open(BytesIO(head))
        im.load()
        im.close()
        return True
    except Exception:
        try:
            upload.seek(0)
        except Exception:
            pass
        return False


def _create_message_with_image_fallback(
    *,
    room,
    sender,
    message_type,
    body,
    save_image,
    save_file,
    save_voice,
    display,
):
    """
    Try normal create; if ImageField rejects the file (e.g. HEIC / odd encodings),
    store the same upload on ``file`` so the attachment is not lost.
    """
    display = (display or "")[:255]
    try:
        return ChatMessage.objects.create(
            room=room,
            sender=sender,
            message_type=message_type,
            body=body,
            image=save_image,
            file=save_file,
            voice=save_voice,
            file_display_name=display,
        )
    except Exception:
        if save_image and not save_file:
            return ChatMessage.objects.create(
                room=room,
                sender=sender,
                message_type=ChatMessage.MessageType.FILE,
                body=body,
                image=None,
                file=save_image,
                voice=save_voice,
                file_display_name=(_upload_basename(save_image) or display or "photo")[:255],
            )
        raise


def _message_payload(request, msg: ChatMessage) -> dict:
    """Shape used by JSON + WebSocket clients (``type`` must be the stored code: image, file, …)."""
    mtype = msg.message_type
    if hasattr(mtype, "value"):
        mtype = mtype.value
    sender = msg.sender
    sender_name = getattr(sender, "name", None) or getattr(sender, "email", "") or ""
    image_url = None
    if msg.image:
        try:
            if msg.image.storage.exists(msg.image.name):
                image_url = request.build_absolute_uri(msg.image.url)
        except Exception:
            image_url = None

    file_url = None
    if msg.file:
        try:
            if msg.file.storage.exists(msg.file.name):
                file_url = request.build_absolute_uri(msg.file.url)
        except Exception:
            file_url = None

    voice_url = None
    if msg.voice:
        try:
            if msg.voice.storage.exists(msg.voice.name):
                voice_url = request.build_absolute_uri(msg.voice.url)
        except Exception:
            voice_url = None

    return {
        "id": msg.pk,
        "type": str(mtype),
        "body": msg.body,
        "sender": sender_name,
        "sender_id": msg.sender_id,
        "created": msg.created_at.isoformat(),
        "image_url": image_url,
        "file_url": file_url,
        "file_name": msg.file_display_name or (_upload_basename(msg.file) if msg.file else ""),
        "voice_url": voice_url,
    }


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


def _mark_media_availability(messages):
    for m in messages:
        m.image_exists = False
        m.file_exists = False
        m.voice_exists = False
        if m.image:
            try:
                m.image_exists = bool(m.image.storage.exists(m.image.name))
            except Exception:
                m.image_exists = False
        if m.file:
            try:
                m.file_exists = bool(m.file.storage.exists(m.file.name))
            except Exception:
                m.file_exists = False
        if m.voice:
            try:
                m.voice_exists = bool(m.voice.storage.exists(m.voice.name))
            except Exception:
                m.voice_exists = False
    return messages


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
            chat_messages = list(
                ChatMessage.objects.filter(room=active)
                .select_related("sender")
                .order_by("created_at")[:200]
            )
            ctx["chat_messages"] = _mark_media_availability(chat_messages)
            ws_scheme = "wss" if request.is_secure() else "ws"
            host = request.get_host()
            payload = {
                "roomId": active.pk,
                "displayTitle": active.display_title(request.user),
                "sendUrl": reverse("chat:send_message", kwargs={"room_id": active.pk}),
                "wsPath": f"/ws/chat/{active.pk}/",
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
            logger.warning(
                "Chat upload validation failed room=%s user=%s errors=%s",
                room.pk,
                request.user.pk,
                form.errors.as_json(),
            )
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
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "error": "empty"}, status=400)
            return redirect(f"{reverse('chat:chat_app')}?room={room.pk}")

        if not display and save_file:
            display = (_upload_basename(save_file) or "")[:255]

        try:
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
            # Ensure saved attachments physically exist; otherwise prevent broken 404 messages.
            missing = []
            if msg.image:
                try:
                    if not msg.image.storage.exists(msg.image.name):
                        missing.append("image")
                except Exception:
                    missing.append("image")
            if msg.file:
                try:
                    if not msg.file.storage.exists(msg.file.name):
                        missing.append("file")
                except Exception:
                    missing.append("file")
            if msg.voice:
                try:
                    if not msg.voice.storage.exists(msg.voice.name):
                        missing.append("voice")
                except Exception:
                    missing.append("voice")
            if missing:
                logger.error(
                    "Chat attachment missing after save room=%s user=%s msg=%s missing=%s",
                    room.pk,
                    request.user.pk,
                    msg.pk,
                    ",".join(missing),
                )
                msg.delete()
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse(
                        {"ok": False, "error": "Attachment upload failed on server storage. Please retry."},
                        status=400,
                    )
                messages.error(request, "Attachment upload failed. Please retry.")
                return redirect(f"{reverse('chat:chat_app')}?room={room.pk}")
        except Exception:
            logger.exception(
                "Chat attachment save failed room=%s user=%s type=%s image=%s file=%s voice=%s",
                room.pk,
                request.user.pk,
                str(msg_type),
                bool(save_image),
                bool(save_file),
                bool(save_voice),
            )
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                detail = "Could not save this attachment. Try another file or format."
                if settings.DEBUG:
                    detail = "Could not save attachment (see server log for traceback)."
                return JsonResponse(
                    {"ok": False, "error": detail},
                    status=400,
                )
            messages.error(request, "Could not save attachment.")
            return redirect(f"{reverse('chat:chat_app')}?room={room.pk}")

        ws_payload = {
            "event": "new_message",
            "message": _message_payload(request, msg),
        }
        broadcast_room_message(room.pk, ws_payload)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"ok": True, **ws_payload})
        return redirect(f"{reverse('chat:chat_app')}?room={room.pk}")

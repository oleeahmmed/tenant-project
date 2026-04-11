from django.contrib import admin

from .models import ChatMember, ChatMessage, ChatRoom


class ChatMemberInline(admin.TabularInline):
    model = ChatMember
    extra = 0


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "kind", "title", "direct_key", "created_at")
    list_filter = ("kind", "tenant")
    inlines = [ChatMemberInline]
    search_fields = ("title", "direct_key")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "sender", "message_type", "created_at")
    list_filter = ("message_type",)

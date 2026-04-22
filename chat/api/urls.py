from django.urls import path

from . import views

app_name = "chat_api"

urlpatterns = [
    path("users/", views.ChatUserListView.as_view(), name="user_list"),
    path("rooms/", views.ChatRoomListView.as_view(), name="room_list"),
    path("rooms/direct/", views.ChatDirectStartView.as_view(), name="room_start_direct"),
    path("rooms/group/", views.ChatGroupCreateView.as_view(), name="room_create_group"),
    path("rooms/<int:room_id>/", views.ChatRoomDetailView.as_view(), name="room_detail"),
    path("rooms/<int:room_id>/messages/", views.ChatMessageListView.as_view(), name="message_list"),
    path("rooms/<int:room_id>/messages/send/", views.ChatMessageCreateView.as_view(), name="message_create"),
]

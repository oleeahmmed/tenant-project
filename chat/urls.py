from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.ChatAppView.as_view(), name="chat_app"),
    path("start/", views.StartDirectView.as_view(), name="start_direct"),
    path("group/", views.GroupCreateView.as_view(), name="create_group"),
    path("room/<int:room_id>/send/", views.PostMessageView.as_view(), name="send_message"),
]

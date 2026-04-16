from django.urls import path

from . import views

app_name = "notification"

urlpatterns = [
    path("", views.NotificationListView.as_view(), name="list"),
    path("<int:pk>/read/", views.NotificationMarkReadView.as_view(), name="mark_read"),
    path("read-all/", views.NotificationMarkAllReadView.as_view(), name="mark_all_read"),
    path("api/unread-count/", views.NotificationUnreadCountApiView.as_view(), name="api_unread_count"),
    path("api/inbox/", views.NotificationInboxApiView.as_view(), name="api_inbox"),
]

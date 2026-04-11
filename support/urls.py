from django.urls import path

from . import views

app_name = "support"

urlpatterns = [
    path("", views.SupportTicketListView.as_view(), name="ticket_list"),
    path("new/", views.SupportTicketCreateView.as_view(), name="ticket_create"),
    path("<int:pk>/", views.SupportTicketDetailView.as_view(), name="ticket_detail"),
]

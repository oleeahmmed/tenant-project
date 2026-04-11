from django.urls import path

from . import views

app_name = "jiraclone"

urlpatterns = [
    path("", views.JiraDashboardView.as_view(), name="jira_dashboard"),
    path("projects/", views.ProjectListView.as_view(), name="project_list"),
    path("projects/create/", views.ProjectCreateView.as_view(), name="project_create"),
    path("project/<str:project_key>/", views.ProjectDetailView.as_view(), name="project_detail"),
    path("project/<str:project_key>/edit/", views.ProjectUpdateView.as_view(), name="project_edit"),
    path("project/<str:project_key>/board/", views.BoardView.as_view(), name="project_board"),
    path("project/<str:project_key>/issues/new/", views.IssueCreateView.as_view(), name="issue_create"),
    path("issue/<str:project_key>/<int:pk>/", views.IssueDetailView.as_view(), name="issue_detail"),
    path("issue/<str:project_key>/<int:pk>/edit/", views.IssueUpdateView.as_view(), name="issue_edit"),
    path("issue/<str:project_key>/<int:pk>/comment/", views.IssueCommentPostView.as_view(), name="issue_comment"),
    path("issue/<str:project_key>/<int:pk>/status/", views.IssueStatusQuickUpdateView.as_view(), name="issue_status_quick"),
]

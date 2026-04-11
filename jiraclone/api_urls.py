from django.urls import path

from . import api_views

app_name = "jiraclone_api"

urlpatterns = [
    path("project/<str:project_key>/board/move/", api_views.BoardMoveApiView.as_view(), name="board_move"),
    path("project/<str:project_key>/statuses/", api_views.StatusesListApiView.as_view(), name="statuses_list"),
    path("project/<str:project_key>/issue/<int:pk>/", api_views.IssueDetailApiView.as_view(), name="issue_detail_json"),
    path(
        "project/<str:project_key>/issue/<int:pk>/comment/",
        api_views.IssueCommentApiView.as_view(),
        name="issue_comment_json",
    ),
    path(
        "project/<str:project_key>/issue/<int:pk>/status/",
        api_views.IssueStatusUpdateApiView.as_view(),
        name="issue_status_json",
    ),
    path(
        "project/<str:project_key>/issue/<int:pk>/fields/",
        api_views.IssueFieldsUpdateApiView.as_view(),
        name="issue_fields_json",
    ),
    path("project/<str:project_key>/subtask/", api_views.SubtaskCreateApiView.as_view(), name="subtask_create"),
    path(
        "project/<str:project_key>/issues/quick-create/",
        api_views.QuickIssueCreateApiView.as_view(),
        name="issue_quick_create",
    ),
]

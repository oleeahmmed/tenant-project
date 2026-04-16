from django.urls import path

from jiraclone.api import views

app_name = "jiraclone_api"

urlpatterns = [
    path("project/<str:project_key>/board/move/", views.BoardMoveApiView.as_view(), name="board_move"),
    path("project/<str:project_key>/statuses/", views.StatusesListApiView.as_view(), name="statuses_list"),
    path("project/<str:project_key>/issue/<int:pk>/", views.IssueDetailApiView.as_view(), name="issue_detail_json"),
    path("project/<str:project_key>/issue/<int:pk>/comment/", views.IssueCommentApiView.as_view(), name="issue_comment_json"),
    path("project/<str:project_key>/issue/<int:pk>/status/", views.IssueStatusUpdateApiView.as_view(), name="issue_status_json"),
    path("project/<str:project_key>/issue/<int:pk>/fields/", views.IssueFieldsUpdateApiView.as_view(), name="issue_fields_json"),
    path("project/<str:project_key>/issue/<int:pk>/inline-update/", views.IssueInlineUpdateApiView.as_view(), name="issue_inline_update"),
    path("project/<str:project_key>/subtask/", views.SubtaskCreateApiView.as_view(), name="subtask_create"),
    path("project/<str:project_key>/issues/quick-create/", views.QuickIssueCreateApiView.as_view(), name="issue_quick_create"),
    path(
        "project/<str:project_key>/department-employees/",
        views.DepartmentEmployeeOptionsApiView.as_view(),
        name="department_employee_options",
    ),
    path(
        "project/<str:project_key>/departments/create/",
        views.DepartmentCreateApiView.as_view(),
        name="department_create",
    ),
    path(
        "project/<str:project_key>/departments/<int:pk>/delete/",
        views.DepartmentDeleteApiView.as_view(),
        name="department_delete",
    ),
    path(
        "project/<str:project_key>/department-assignments/",
        views.DepartmentAssignmentListCreateApiView.as_view(),
        name="department_assignment_list_create",
    ),
    path(
        "project/<str:project_key>/department-assignments/<int:pk>/",
        views.DepartmentAssignmentDetailApiView.as_view(),
        name="department_assignment_detail",
    ),
]

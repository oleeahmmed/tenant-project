from django.urls import path

from . import views

urlpatterns = [
    path("jobs/", views.recruitment_job_list, name="recruitment_job_list"),
    path("jobs/add/", views.recruitment_job_create, name="recruitment_job_create"),
    path("jobs/<int:pk>/edit/", views.recruitment_job_edit, name="recruitment_job_edit"),
    path("jobs/<int:pk>/delete/", views.recruitment_job_delete, name="recruitment_job_delete"),
    path("applications/", views.recruitment_application_list, name="recruitment_application_list"),
    path("applications/add/", views.recruitment_application_create, name="recruitment_application_create"),
    path("applications/<int:pk>/edit/", views.recruitment_application_edit, name="recruitment_application_edit"),
    path("applications/<int:pk>/delete/", views.recruitment_application_delete, name="recruitment_application_delete"),
]

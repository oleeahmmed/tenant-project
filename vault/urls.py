from django.urls import path

from . import views

app_name = "vault"

urlpatterns = [
    path("", views.VaultDashboardView.as_view(), name="dashboard"),
    path("customers/", views.VaultCustomerListView.as_view(), name="customer_list"),
    path("customers/<int:pk>/", views.VaultCustomerDetailView.as_view(), name="customer_detail"),
    path("projects/<str:project_key>/", views.VaultProjectDetailView.as_view(), name="project_detail"),
    path("categories/", views.VaultCategoryListView.as_view(), name="category_list"),
    path("categories/add/", views.VaultCategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/edit/", views.VaultCategoryUpdateView.as_view(), name="category_edit"),
    path("entries/", views.VaultEntryListView.as_view(), name="entry_list"),
    path("entries/add/", views.VaultEntryCreateView.as_view(), name="entry_create"),
    path("entries/<int:pk>/", views.VaultEntryDetailView.as_view(), name="entry_detail"),
    path("entries/<int:pk>/edit/", views.VaultEntryUpdateView.as_view(), name="entry_edit"),
    path("entries/<int:pk>/reveal/", views.VaultEntryRevealPasswordView.as_view(), name="entry_reveal"),
    path("entries/<int:pk>/hide-password/", views.VaultEntryHidePasswordView.as_view(), name="entry_hide_password"),
    path("entries/<int:pk>/attachments/add/", views.VaultEntryAttachmentCreateView.as_view(), name="entry_attachment"),
    path("entries/<int:pk>/share/", views.VaultEntryShareCreateView.as_view(), name="entry_share"),
]

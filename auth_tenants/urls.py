from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/',       views.login_view,      name='login'),
    path('register/',    views.register_view,   name='register'),
    path('verify-otp/',  views.verify_otp_view, name='verify_otp'),
    path('logout/',      views.logout_view,     name='logout'),
    path('profile/',     views.profile_view,    name='profile'),

    # Invite accept (public)
    path('invite/<uuid:token>/', views.invite_accept_view, name='invite_accept'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Members
    path('dashboard/members/',                       views.members_view,            name='members'),
    path('dashboard/members/<int:pk>/role/',         views.member_role_view,        name='member_role'),
    path('dashboard/members/<int:pk>/delete/',       views.member_delete_view,      name='member_delete'),
    path('dashboard/members/<int:pk>/permissions/',  views.member_permissions_view, name='member_permissions'),

    # Roles
    path('dashboard/roles/',              views.roles_view,       name='roles'),
    path('dashboard/roles/create/',       views.role_create_view, name='role_create'),
    path('dashboard/roles/<int:pk>/update/', views.role_update_view, name='role_update'),
    path('dashboard/roles/<int:pk>/delete/', views.role_delete_view, name='role_delete'),

    # Invitations
    path('dashboard/invitations/',              views.invitations_view,        name='invitations'),
    path('dashboard/invitations/create/',       views.invitation_create_view,  name='invitation_create'),
    path('dashboard/invitations/<int:pk>/cancel/', views.invitation_cancel_view, name='invitation_cancel'),

    # Super Admin
    path('dashboard/tenants/',     views.tenant_list_view,     name='tenant_list'),
    path('dashboard/tenants/<int:tenant_id>/access/', views.tenant_access_matrix_view, name='tenant_access_matrix'),
    path('dashboard/permissions/', views.permission_list_view, name='permission_list'),
    
    # Subscription Management
    path('dashboard/subscription/', views.subscription_dashboard, name='subscription_dashboard'),
]

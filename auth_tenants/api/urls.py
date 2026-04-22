from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from .views import (
    RegisterView, VerifyOTPView, AcceptInvitationView, MeView, WorkspaceContextView,
    TenantMeView, TenantCompanySettingsApiView,
    PermissionListView, PermissionDetailView,
    RoleListView, RoleDetailView,
    InvitationListView, InvitationCancelView,
    MemberListView, MemberDetailView, MemberPermissionView,
    TenantListView,
)
from .subscription_views import (
    SubscriptionPlansView, TenantSubscriptionView, SubscriptionUsageView,
    PaymentProcessView, PaymentHistoryView
)

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────────────
    path("register/",              RegisterView.as_view()),
    path("verify-otp/",            VerifyOTPView.as_view()),
    path("login/",                 TokenObtainPairView.as_view()),
    path("token/refresh/",         TokenRefreshView.as_view()),
    path("logout/",                TokenBlacklistView.as_view()),
    path("me/",                    MeView.as_view()),
    path("workspace/context/",     WorkspaceContextView.as_view()),

    # ── Invitation (public) ───────────────────────────────────────────────────
    path("invite/<uuid:token>/",   AcceptInvitationView.as_view()),

    # ── Tenant ────────────────────────────────────────────────────────────────
    path("tenant/me/",             TenantMeView.as_view()),
    path("tenant/company-settings/", TenantCompanySettingsApiView.as_view()),

    # ── Permission Master List (GET: tenant admin, POST/PATCH/DELETE: super admin)
    path("permissions/",               PermissionListView.as_view()),
    path("permissions/<int:pk>/",      PermissionDetailView.as_view()),

    # ── Roles ─────────────────────────────────────────────────────────────────
    path("tenant/roles/",          RoleListView.as_view()),
    path("tenant/roles/<int:pk>/", RoleDetailView.as_view()),

    # ── Invitations ───────────────────────────────────────────────────────────
    path("tenant/invitations/",            InvitationListView.as_view()),
    path("tenant/invitations/<int:pk>/",   InvitationCancelView.as_view()),

    # ── Members ───────────────────────────────────────────────────────────────
    path("tenant/members/",                        MemberListView.as_view()),
    path("tenant/members/<int:pk>/",               MemberDetailView.as_view()),
    path("tenant/members/<int:pk>/permissions/",   MemberPermissionView.as_view()),

    # ── Super Admin ───────────────────────────────────────────────────────────
    path("tenants/",               TenantListView.as_view()),
    
    # ── Subscription Management ───────────────────────────────────────────────
    path("subscription/plans/",           SubscriptionPlansView.as_view()),
    path("subscription/current/",         TenantSubscriptionView.as_view()),
    path("subscription/upgrade/",         TenantSubscriptionView.as_view()),
    path("subscription/usage/",           SubscriptionUsageView.as_view()),
    path("subscription/payment/",         PaymentProcessView.as_view()),
    path("subscription/payment-history/", PaymentHistoryView.as_view()),
]

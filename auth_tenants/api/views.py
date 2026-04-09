from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from hrm.tenant_scope import get_hrm_tenant

from auth_tenants.models import Tenant, Role, Invitation, Permission
from .serializers import (
    RegisterSerializer, VerifyOTPSerializer, AcceptInvitationSerializer,
    UserSerializer, TenantSerializer, RoleSerializer,
    InvitationCreateSerializer, InvitationSerializer,
    PermissionSerializer, MemberPermissionSerializer,
)
from .permissions import IsSuperAdmin, IsTenantAdmin

User = get_user_model()


def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


# ── Register ──────────────────────────────────────────────────────────────────
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(
            {"detail": "Registration successful. Check your email for OTP."},
            status=status.HTTP_201_CREATED,
        )


# ── OTP Verify ────────────────────────────────────────────────────────────────
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = VerifyOTPSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        otp  = s.validated_data["otp_obj"]
        user = User.objects.get(email=otp.email)
        otp.is_used    = True
        otp.save()
        user.is_active = True
        user.save()
        return Response(get_tokens(user))


# ── Accept Invitation ─────────────────────────────────────────────────────────
class AcceptInvitationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            invite = Invitation.objects.select_related("tenant", "role").get(token=token)
        except Invitation.DoesNotExist:
            return Response({"detail": "Invalid token."}, status=status.HTTP_404_NOT_FOUND)
        if not invite.is_valid():
            return Response({"detail": "Invitation expired or already accepted."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "email":  invite.email,
            "name":   invite.name,
            "tenant": invite.tenant.name,
            "role":   invite.role.name if invite.role else None,
        })

    def post(self, request, token):
        s = AcceptInvitationSerializer(
            data={**request.data, "token": str(token)},
            context={},
        )
        s.is_valid(raise_exception=True)
        user = s.save()
        return Response(get_tokens(user), status=status.HTTP_201_CREATED)


# ── Me ────────────────────────────────────────────────────────────────────────
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


# ── Tenant Profile ────────────────────────────────────────────────────────────
class TenantMeView(APIView):
    permission_classes = [IsTenantAdmin]

    def get(self, request):
        tenant = get_hrm_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "No workspace tenant resolved for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(TenantSerializer(tenant).data)

    def patch(self, request):
        tenant = get_hrm_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "No workspace tenant resolved for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        s = TenantSerializer(tenant, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)


# ── Permission Master List (Super Admin) ──────────────────────────────────────
class PermissionListView(APIView):
    """Super Admin সব permission define করবে এখানে।"""

    def get_permissions(self):
        # GET — tenant admin ও দেখতে পারবে (role বানাতে কাজে লাগবে)
        if self.request.method == "GET":
            return [IsTenantAdmin()]
        return [IsSuperAdmin()]

    def get(self, request):
        perms = Permission.objects.filter(is_active=True)
        # category দিয়ে filter করা যাবে: ?category=contacts
        category = request.query_params.get("category")
        if category:
            perms = perms.filter(category=category)
        return Response(PermissionSerializer(perms, many=True).data)

    def post(self, request):
        s = PermissionSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data, status=status.HTTP_201_CREATED)


class PermissionDetailView(APIView):
    permission_classes = [IsSuperAdmin]

    def _get(self, pk):
        try:
            return Permission.objects.get(pk=pk)
        except Permission.DoesNotExist:
            return None

    def patch(self, request, pk):
        perm = self._get(pk)
        if not perm:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        s = PermissionSerializer(perm, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)

    def delete(self, request, pk):
        perm = self._get(pk)
        if not perm:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        # Hard delete না করে deactivate করো — existing role এ থাকলে সমস্যা হবে না
        perm.is_active = False
        perm.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Role Management ───────────────────────────────────────────────────────────
class RoleListView(APIView):
    permission_classes = [IsTenantAdmin]

    def get(self, request):
        tenant = get_hrm_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "No workspace tenant resolved for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        roles = Role.objects.filter(tenant=tenant).prefetch_related("permissions")
        return Response(RoleSerializer(roles, many=True).data)

    def post(self, request):
        tenant = get_hrm_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "No workspace tenant resolved for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        s = RoleSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        s.save(tenant=tenant)
        return Response(s.data, status=status.HTTP_201_CREATED)


class RoleDetailView(APIView):
    permission_classes = [IsTenantAdmin]

    def _get(self, pk, tenant):
        try:
            return Role.objects.prefetch_related("permissions").get(pk=pk, tenant=tenant)
        except Role.DoesNotExist:
            return None

    def get(self, request, pk):
        tenant = get_hrm_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "No workspace tenant resolved for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        role = self._get(pk, tenant)
        if not role:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(RoleSerializer(role).data)

    def patch(self, request, pk):
        tenant = get_hrm_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "No workspace tenant resolved for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        role = self._get(pk, tenant)
        if not role:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        s = RoleSerializer(role, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)

    def delete(self, request, pk):
        tenant = get_hrm_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "No workspace tenant resolved for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        role = self._get(pk, tenant)
        if not role:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Invitation Management ─────────────────────────────────────────────────────
class InvitationListView(APIView):
    permission_classes = [IsTenantAdmin]

    def get(self, request):
        tenant = get_hrm_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "No workspace tenant resolved for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        invites = Invitation.objects.filter(tenant=tenant).order_by("-created_at")
        return Response(InvitationSerializer(invites, many=True).data)

    def post(self, request):
        tenant = get_hrm_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "No workspace tenant resolved for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        s = InvitationCreateSerializer(
            data=request.data,
            context={"tenant": tenant, "invited_by": request.user},
        )
        s.is_valid(raise_exception=True)
        invite = s.save()
        return Response(InvitationSerializer(invite).data, status=status.HTTP_201_CREATED)


class InvitationCancelView(APIView):
    permission_classes = [IsTenantAdmin]

    def delete(self, request, pk):
        tenant = get_hrm_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "No workspace tenant resolved for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            invite = Invitation.objects.get(pk=pk, tenant=tenant, is_accepted=False)
        except Invitation.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        invite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Member Management ─────────────────────────────────────────────────────────
class MemberListView(APIView):
    permission_classes = [IsTenantAdmin]

    def get(self, request):
        tenant = get_hrm_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "No workspace tenant resolved for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        members = User.objects.filter(
            tenant=tenant, role="staff"
        ).select_related("custom_role").prefetch_related("extra_permissions")
        return Response(UserSerializer(members, many=True).data)


class MemberDetailView(APIView):
    permission_classes = [IsTenantAdmin]

    def _get(self, pk, tenant):
        try:
            return User.objects.select_related("custom_role").prefetch_related(
                "extra_permissions"
            ).get(pk=pk, tenant=tenant, role="staff")
        except User.DoesNotExist:
            return None

    def patch(self, request, pk):
        """Member এর role পরিবর্তন করো"""
        tenant = get_hrm_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "No workspace tenant resolved for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        member = self._get(pk, tenant)
        if not member:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        role_id = request.data.get("role_id")
        if role_id is not None:
            if role_id == "" or role_id is None:
                member.custom_role = None
            else:
                try:
                    role = Role.objects.get(pk=role_id, tenant=tenant)
                except Role.DoesNotExist:
                    return Response({"detail": "Role not found."}, status=status.HTTP_400_BAD_REQUEST)
                member.custom_role = role
            member.save()
        return Response(UserSerializer(member).data)

    def delete(self, request, pk):
        tenant = get_hrm_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "No workspace tenant resolved for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        member = self._get(pk, tenant)
        if not member:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MemberPermissionView(APIView):
    """
    Member এর extra_permissions directly add/remove করো।
    Role এর বাইরে individual permission control।
    """
    permission_classes = [IsTenantAdmin]

    def _get_member(self, pk, tenant):
        try:
            return User.objects.prefetch_related("extra_permissions").get(
                pk=pk, tenant=tenant, role="staff"
            )
        except User.DoesNotExist:
            return None

    def get(self, request, pk):
        """Member এর current extra permissions দেখো"""
        tenant = get_hrm_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "No workspace tenant resolved for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        member = self._get_member(pk, tenant)
        if not member:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({
            "member_id":        member.id,
            "member_name":      member.name,
            "role":             member.custom_role.name if member.custom_role else None,
            "role_permissions": PermissionSerializer(
                member.custom_role.permissions.filter(is_active=True), many=True
            ).data if member.custom_role else [],
            "extra_permissions": PermissionSerializer(
                member.extra_permissions.filter(is_active=True), many=True
            ).data,
            "effective_permissions": sorted(member.get_all_permissions_set()),
        })

    def post(self, request, pk):
        """Extra permission add ও remove করো একসাথে"""
        tenant = get_hrm_tenant(request)
        if tenant is None:
            return Response(
                {"detail": "No workspace tenant resolved for this account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        member = self._get_member(pk, tenant)
        if not member:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        s = MemberPermissionSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        to_add    = s.validated_data.get("add_permission_ids", [])
        to_remove = s.validated_data.get("remove_permission_ids", [])

        if to_add:
            member.extra_permissions.add(*to_add)
        if to_remove:
            member.extra_permissions.remove(*to_remove)

        # Updated state return করো
        member.refresh_from_db()
        return Response({
            "member_id":         member.id,
            "extra_permissions": PermissionSerializer(
                member.extra_permissions.filter(is_active=True), many=True
            ).data,
            "effective_permissions": sorted(member.get_all_permissions_set()),
        })


# ── Super Admin — All Tenants ─────────────────────────────────────────────────
class TenantListView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        return Response(TenantSerializer(Tenant.objects.all(), many=True).data)

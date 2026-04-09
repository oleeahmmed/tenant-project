from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST

from hrm.tenant_scope import get_hrm_tenant, user_belongs_to_workspace_tenant

from .models import User, Tenant, Role, Invitation, OTPVerification, Permission
from .api.utils import send_otp_email, send_invitation_email


def _get_tenant_or_redirect(request):
    """
    Same tenant resolution as HRM / Foundation (session, user.tenant, employee profile, …).
    """
    tenant = get_hrm_tenant(request)
    if tenant is not None:
        return tenant
    messages.error(
        request,
        "No workspace tenant is available. Open Human Resources and select a company, "
        "or ask an admin to link your account to a tenant or employee profile.",
    )
    return None


def _tenant_mgmt_guard(request):
    """
    For Members / Roles / Invitations: require a resolved tenant and membership.
    Returns ``tenant`` or ``None`` (after setting messages).
    """
    tenant = get_hrm_tenant(request)
    if tenant is None:
        messages.error(
            request,
            "No workspace tenant is available. Open Human Resources and select a company, "
            "or ask an admin to link your account to a tenant or employee profile.",
        )
        return None
    if not user_belongs_to_workspace_tenant(request.user, tenant):
        messages.error(request, "You do not have access to manage this workspace.")
        return None
    return tenant


# ── Auth ──────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    error = None
    if request.method == 'POST':
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        error = 'Invalid email or password.'
    return render(request, 'auth_tenants/login.html', {'error': error})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    error = None
    form_data = {}
    if request.method == 'POST':
        form_data = request.POST
        from .api.serializers import RegisterSerializer
        s = RegisterSerializer(data={
            'name':         request.POST.get('name', '').strip(),
            'email':        request.POST.get('email', '').strip(),
            'password':     request.POST.get('password', ''),
            'company_name': request.POST.get('company_name', '').strip(),
        })
        if s.is_valid():
            user = s.save()
            return redirect(f'/verify-otp/?email={user.email}')
        error = list(s.errors.values())[0][0]
    return render(request, 'auth_tenants/register.html', {'error': error, 'form_data': form_data})


def verify_otp_view(request):
    email = request.GET.get('email') or request.POST.get('email', '')
    error = None
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()
        try:
            otp = OTPVerification.objects.filter(email=email, otp_code=otp_code).latest('created_at')
        except OTPVerification.DoesNotExist:
            error = 'Invalid OTP.'
        else:
            if not otp.is_valid():
                error = 'OTP expired or already used.'
            else:
                otp.is_used = True
                otp.save()
                user = User.objects.get(email=email)
                user.is_active = True
                user.save()
                login(request, user)
                return redirect('dashboard')
    return render(request, 'auth_tenants/verify_otp.html', {'email': email, 'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        name   = request.POST.get('name', '').strip()
        avatar = request.FILES.get('avatar')
        if name:
            request.user.name = name
        if avatar:
            request.user.avatar = avatar
        request.user.save()
        messages.success(request, "Profile updated.")
        return redirect('profile')
    return render(request, 'auth_tenants/profile.html', {})


# ── Dashboard ─────────────────────────────────────────────────────────────────

@login_required
def dashboard_view(request):
    user = request.user
    stats = {}
    if user.role == 'super_admin':
        stats['total_tenants'] = Tenant.objects.count()
    workspace = get_hrm_tenant(request)
    if workspace and user.role in ('super_admin', 'tenant_admin'):
        stats['total_members'] = User.objects.filter(tenant=workspace, role='staff').count()
        stats['total_roles'] = Role.objects.filter(tenant=workspace).count()
        stats['pending_invites'] = Invitation.objects.filter(
            tenant=workspace, is_accepted=False, expires_at__gt=timezone.now()
        ).count()
    my_permissions = sorted(user.get_all_permissions_set()) if user.role == 'staff' else []
    return render(request, 'auth_tenants/dashboard.html', {
        'active_page':    'dashboard',
        'stats':          stats,
        'my_permissions': my_permissions,
    })


# ── Members ───────────────────────────────────────────────────────────────────

@login_required
def members_view(request):
    if request.user.role not in ('super_admin', 'tenant_admin'):
        return redirect('dashboard')
    tenant = _tenant_mgmt_guard(request)
    if tenant is None:
        return redirect('dashboard')
    members = User.objects.filter(
        tenant=tenant, role='staff'
    ).select_related('custom_role').prefetch_related('extra_permissions', 'custom_role__permissions')
    roles = Role.objects.filter(tenant=tenant)
    return render(request, 'auth_tenants/members.html', {
        'active_page': 'members',
        'members':     members,
        'roles':       roles,
    })


@login_required
@require_POST
def member_role_view(request, pk):
    if request.user.role not in ('super_admin', 'tenant_admin'):
        return redirect('dashboard')
    tenant = _tenant_mgmt_guard(request)
    if tenant is None:
        return redirect('dashboard')
    member  = get_object_or_404(User, pk=pk, tenant=tenant, role='staff')
    role_id = request.POST.get('role_id')
    if role_id:
        role = get_object_or_404(Role, pk=role_id, tenant=tenant)
        member.custom_role = role
    else:
        member.custom_role = None
    member.save()
    messages.success(request, f"Role updated for {member.name}.")
    return redirect('members')


@login_required
@require_POST
def member_delete_view(request, pk):
    if request.user.role not in ('super_admin', 'tenant_admin'):
        return redirect('dashboard')
    tenant = _tenant_mgmt_guard(request)
    if tenant is None:
        return redirect('dashboard')
    member = get_object_or_404(User, pk=pk, tenant=tenant, role='staff')
    name   = member.name
    member.delete()
    messages.success(request, f"{name} removed.")
    return redirect('members')


@login_required
def member_permissions_view(request, pk):
    if request.user.role not in ('super_admin', 'tenant_admin'):
        return redirect('dashboard')
    tenant = _tenant_mgmt_guard(request)
    if tenant is None:
        return redirect('dashboard')
    member = get_object_or_404(
        User.objects.prefetch_related('extra_permissions', 'custom_role__permissions'),
        pk=pk, tenant=tenant, role='staff'
    )
    all_permissions = Permission.objects.filter(is_active=True)

    if request.method == 'POST':
        selected_ids = request.POST.getlist('add_ids')
        # selected olan গুলো set করো, বাকিগুলো remove হবে
        member.extra_permissions.set(Permission.objects.filter(pk__in=selected_ids, is_active=True))
        messages.success(request, "Permissions updated.")
        return redirect('member_permissions', pk=pk)

    return render(request, 'auth_tenants/member_permissions.html', {
        'active_page':   'members',
        'member':        member,
        'all_permissions': all_permissions,
        'extra_perm_ids':  set(member.extra_permissions.values_list('id', flat=True)),
        'effective':       sorted(member.get_all_permissions_set()),
    })


# ── Roles ─────────────────────────────────────────────────────────────────────

@login_required
def roles_view(request):
    if request.user.role not in ('super_admin', 'tenant_admin'):
        return redirect('dashboard')
    tenant = _get_tenant_or_redirect(request)
    if not tenant:
        return redirect('dashboard')
    roles           = Role.objects.filter(tenant=tenant).prefetch_related('permissions')
    all_permissions = Permission.objects.filter(is_active=True).order_by('category', 'codename')
    return render(request, 'auth_tenants/roles.html', {
        'active_page':    'roles',
        'roles':          roles,
        'all_permissions': all_permissions,
    })


@login_required
@require_POST
def role_create_view(request):
    if request.user.role not in ('super_admin', 'tenant_admin'):
        return redirect('dashboard')
    tenant = _get_tenant_or_redirect(request)
    if not tenant:
        return redirect('dashboard')
    name     = request.POST.get('name', '').strip()
    perm_ids = request.POST.getlist('permission_ids')
    if name:
        role, _ = Role.objects.get_or_create(name=name, tenant=tenant)
        role.permissions.set(Permission.objects.filter(pk__in=perm_ids, is_active=True))
        messages.success(request, f"Role '{name}' created.")
    return redirect('roles')


@login_required
@require_POST
def role_delete_view(request, pk):
    if request.user.role not in ('super_admin', 'tenant_admin'):
        return redirect('dashboard')
    tenant = _get_tenant_or_redirect(request)
    if not tenant:
        return redirect('dashboard')
    role = get_object_or_404(Role, pk=pk, tenant=tenant)
    role.delete()
    messages.success(request, "Role deleted.")
    return redirect('roles')


@login_required
@require_POST
def role_update_view(request, pk):
    if request.user.role not in ('super_admin', 'tenant_admin'):
        return redirect('dashboard')
    tenant = _get_tenant_or_redirect(request)
    if not tenant:
        return redirect('dashboard')
    role = get_object_or_404(Role, pk=pk, tenant=tenant)
    name = request.POST.get('name', '').strip()
    if name:
        role.name = name
        role.save(update_fields=['name'])
        messages.success(request, "Role updated.")
    else:
        messages.error(request, "Role name is required.")
    return redirect('roles')


# ── Invitations ───────────────────────────────────────────────────────────────

@login_required
def invitations_view(request):
    if request.user.role not in ('super_admin', 'tenant_admin'):
        return redirect('dashboard')
    tenant = _tenant_mgmt_guard(request)
    if tenant is None:
        return redirect('dashboard')
    invitations = Invitation.objects.filter(
        tenant=tenant
    ).select_related('role').order_by('-created_at')
    roles = Role.objects.filter(tenant=tenant)
    return render(request, 'auth_tenants/invitations.html', {
        'active_page': 'invitations',
        'invitations': invitations,
        'roles':       roles,
    })


@login_required
@require_POST
def invitation_create_view(request):
    if request.user.role not in ('super_admin', 'tenant_admin'):
        return redirect('dashboard')
    tenant = _tenant_mgmt_guard(request)
    if tenant is None:
        return redirect('dashboard')
    from .api.serializers import InvitationCreateSerializer
    s = InvitationCreateSerializer(
        data={
            'name':    request.POST.get('name', '').strip(),
            'email':   request.POST.get('email', '').strip(),
            'role_id': request.POST.get('role_id') or None,
        },
        context={'tenant': tenant, 'invited_by': request.user, 'request': request},
    )
    if s.is_valid():
        s.save()
        messages.success(request, "Invitation sent.")
    else:
        err = list(s.errors.values())[0][0]
        messages.error(request, str(err))
    return redirect('invitations')


@login_required
@require_POST
def invitation_cancel_view(request, pk):
    if request.user.role not in ('super_admin', 'tenant_admin'):
        return redirect('dashboard')
    tenant = _tenant_mgmt_guard(request)
    if tenant is None:
        return redirect('dashboard')
    invite = get_object_or_404(Invitation, pk=pk, tenant=tenant, is_accepted=False)
    invite.delete()
    messages.success(request, "Invitation cancelled.")
    return redirect('invitations')


def invite_accept_view(request, token):
    try:
        invite = Invitation.objects.select_related('tenant', 'role').get(token=token)
    except Invitation.DoesNotExist:
        return render(request, 'auth_tenants/invite_accept.html', {
            'invalid': True, 'error': 'Invalid invitation link.'
        })
    if not invite.is_valid():
        return render(request, 'auth_tenants/invite_accept.html', {
            'invalid': True, 'error': 'Invitation expired or already accepted.'
        })

    error = None
    if request.method == 'POST':
        password = request.POST.get('password', '')
        if len(password) < 8:
            error = 'Password must be at least 8 characters.'
        else:
            user = User.objects.create_user(
                email=invite.email, password=password,
                name=invite.name, role='staff',
                tenant=invite.tenant, custom_role=invite.role,
                is_active=True,
            )
            invite.is_accepted = True
            invite.save()
            login(request, user)
            return redirect('dashboard')

    return render(request, 'auth_tenants/invite_accept.html', {'invite': invite, 'error': error})


# ── Super Admin ───────────────────────────────────────────────────────────────

@login_required
def tenant_list_view(request):
    if request.user.role != 'super_admin':
        return redirect('dashboard')
    tenants = Tenant.objects.all().order_by('-created_at')
    return render(request, 'auth_tenants/tenant_list.html', {
        'active_page': 'tenants',
        'tenants':     tenants,
    })


@login_required
def permission_list_view(request):
    if request.user.role != 'super_admin':
        return redirect('dashboard')
    error = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            codename = request.POST.get('codename', '').strip()
            label    = request.POST.get('label', '').strip()
            category = request.POST.get('category', '').strip()
            if codename and label and category:
                Permission.objects.get_or_create(
                    codename=codename,
                    defaults={'label': label, 'category': category}
                )
                messages.success(request, f"Permission '{codename}' created.")
            else:
                error = 'All fields are required.'
        elif action == 'deactivate':
            pk = request.POST.get('pk')
            Permission.objects.filter(pk=pk).update(is_active=False)
            messages.success(request, "Permission deactivated.")
        elif action == 'activate':
            pk = request.POST.get('pk')
            Permission.objects.filter(pk=pk).update(is_active=True)
            messages.success(request, "Permission activated.")
        return redirect('permission_list')

    permissions = Permission.objects.all().order_by('category', 'codename')
    return render(request, 'auth_tenants/permission_list.html', {
        'active_page': 'permissions',
        'permissions': permissions,
        'categories':  Permission.CATEGORIES,
        'error':       error,
    })

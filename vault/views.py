from django.contrib import messages
from django.core.signing import BadSignature, SignatureExpired
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from foundation.models import Customer
from jiraclone.models import JiraProject

from .forms import VaultCategoryForm, VaultEntryForm, VaultFileAttachmentForm, VaultShareForm
from .mixins import VaultAdminMixin, VaultDashboardAccessMixin, VaultPageContextMixin
from .models import VaultCategory, VaultEntry, VaultFileAttachment, VaultSharedEntry
from .services import send_vault_share_invite_email, share_record_is_usable, vault_share_parse_token


class VaultDashboardView(VaultDashboardAccessMixin, VaultPageContextMixin, TemplateView):
    template_name = "vault/dashboard.html"
    page_title = "Credential Vault"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = self.request.hrm_tenant
        category_qs = VaultCategory.objects.filter(tenant=tenant, is_active=True)
        entry_qs = VaultEntry.objects.filter(tenant=tenant)
        ctx["category_count"] = category_qs.count()
        ctx["entry_count"] = entry_qs.count()
        ctx["favorite_count"] = entry_qs.filter(is_favorite=True).count()
        ctx["top_customers"] = (
            category_qs.values("customer__name")
            .annotate(total=Count("entries"))
            .order_by("-total", "customer__name")[:5]
        )
        return ctx


class VaultCustomerListView(VaultDashboardAccessMixin, VaultPageContextMixin, ListView):
    model = Customer
    template_name = "vault/customer_list.html"
    context_object_name = "customers"
    page_title = "Vault customers"

    def get_queryset(self):
        tenant = self.request.hrm_tenant
        q = (self.request.GET.get("q") or "").strip()
        qs = Customer.objects.filter(tenant=tenant, is_active=True)
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(customer_code__icontains=q) | Q(email__icontains=q))
        return qs.order_by("name")


class VaultCustomerDetailView(VaultDashboardAccessMixin, VaultPageContextMixin, DetailView):
    model = Customer
    template_name = "vault/customer_detail.html"
    context_object_name = "customer"
    page_title = "Customer vault details"

    def get_queryset(self):
        return Customer.objects.filter(tenant=self.request.hrm_tenant, is_active=True)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        customer = self.object
        tenant = self.request.hrm_tenant
        projects = JiraProject.objects.filter(tenant=tenant, customer=customer, is_active=True).order_by("key")
        categories = (
            VaultCategory.objects.filter(tenant=tenant, customer=customer)
            .order_by("name")
        )
        ctx["projects"] = projects
        ctx["categories"] = categories
        return ctx


class VaultProjectDetailView(VaultDashboardAccessMixin, VaultPageContextMixin, DetailView):
    model = JiraProject
    template_name = "vault/project_detail.html"
    context_object_name = "project"
    page_title = "Project vault details"
    slug_field = "key"
    slug_url_kwarg = "project_key"

    def get_queryset(self):
        return JiraProject.objects.filter(tenant=self.request.hrm_tenant).select_related("customer")

    def get_object(self, queryset=None):
        qs = self.get_queryset() if queryset is None else queryset
        key = (self.kwargs.get("project_key") or "").strip().upper()
        return get_object_or_404(qs, key=key)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project = self.object
        customer = project.customer
        categories = VaultCategory.objects.filter(
            tenant=self.request.hrm_tenant,
            customer=customer,
        ).order_by("name")
        entries = VaultEntry.objects.filter(
            tenant=self.request.hrm_tenant,
            category__customer=customer,
            project=project,
        ).select_related("category", "project").order_by("category__name", "name")
        ctx["categories"] = categories
        ctx["entries"] = entries
        return ctx


class VaultCategoryListView(VaultDashboardAccessMixin, VaultPageContextMixin, ListView):
    model = VaultCategory
    template_name = "vault/category_list.html"
    context_object_name = "categories"
    page_title = "Vault categories"

    def get_queryset(self):
        tenant = self.request.hrm_tenant
        q = (self.request.GET.get("q") or "").strip()
        qs = VaultCategory.objects.filter(tenant=tenant).select_related("customer")
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(customer__name__icontains=q)
            )
        return qs.order_by("customer__name", "name")


class VaultCategoryCreateView(VaultAdminMixin, VaultPageContextMixin, CreateView):
    model = VaultCategory
    form_class = VaultCategoryForm
    template_name = "vault/category_form.html"
    page_title = "Add category"
    success_url = reverse_lazy("vault:category_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        kwargs["selected_customer_id"] = (self.request.GET.get("customer") or "").strip() or None
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Category created.")
        return redirect(self.success_url)


class VaultCategoryUpdateView(VaultAdminMixin, VaultPageContextMixin, UpdateView):
    model = VaultCategory
    form_class = VaultCategoryForm
    template_name = "vault/category_form.html"
    context_object_name = "category"
    page_title = "Edit category"
    success_url = reverse_lazy("vault:category_list")

    def get_queryset(self):
        return VaultCategory.objects.filter(tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Category updated.")
        return super().form_valid(form)


class VaultEntryListView(VaultDashboardAccessMixin, VaultPageContextMixin, ListView):
    model = VaultEntry
    template_name = "vault/entry_list.html"
    context_object_name = "entries"
    page_title = "Vault entries"

    def get_queryset(self):
        tenant = self.request.hrm_tenant
        q = (self.request.GET.get("q") or "").strip()
        category_id = (self.request.GET.get("category") or "").strip()
        qs = VaultEntry.objects.filter(tenant=tenant).select_related(
            "category", "category__customer", "project"
        )
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(url__icontains=q)
                | Q(username__icontains=q)
                | Q(category__customer__name__icontains=q)
                | Q(project__name__icontains=q)
                | Q(project__key__icontains=q)
            )
        if category_id.isdigit():
            qs = qs.filter(category_id=int(category_id))
        return qs.order_by("category__customer__name", "project__key", "category__name", "name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = VaultCategory.objects.filter(tenant=self.request.hrm_tenant, is_active=True).order_by("name")
        ctx["selected_category"] = self.request.GET.get("category", "")
        ctx["search_query"] = self.request.GET.get("q", "")
        return ctx


class VaultEntryCreateView(VaultAdminMixin, VaultPageContextMixin, CreateView):
    model = VaultEntry
    form_class = VaultEntryForm
    template_name = "vault/entry_form.html"
    page_title = "Add credential entry"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        kwargs["selected_customer_id"] = (self.request.GET.get("customer") or "").strip() or None
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.created_by = self.request.user
        self.object.updated_by = self.request.user
        self.object.set_password(form.cleaned_data.get("password") or "")
        self.object.save()
        attachment_file = form.cleaned_data.get("attachment_file")
        if attachment_file:
            VaultFileAttachment.objects.create(
                tenant=self.request.hrm_tenant,
                entry=self.object,
                file=attachment_file,
                title=(form.cleaned_data.get("attachment_title") or "").strip(),
            )
        messages.success(self.request, "Credential entry created.")
        return redirect("vault:entry_detail", pk=self.object.pk)


class VaultEntryUpdateView(VaultAdminMixin, VaultPageContextMixin, UpdateView):
    model = VaultEntry
    form_class = VaultEntryForm
    template_name = "vault/entry_form.html"
    context_object_name = "entry"
    page_title = "Edit credential entry"

    def get_queryset(self):
        return VaultEntry.objects.filter(tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.updated_by = self.request.user
        password = (form.cleaned_data.get("password") or "").strip()
        if password:
            self.object.set_password(password)
        self.object.save()
        attachment_file = form.cleaned_data.get("attachment_file")
        if attachment_file:
            VaultFileAttachment.objects.create(
                tenant=self.request.hrm_tenant,
                entry=self.object,
                file=attachment_file,
                title=(form.cleaned_data.get("attachment_title") or "").strip(),
            )
        messages.success(self.request, "Credential entry updated.")
        return redirect("vault:entry_detail", pk=self.object.pk)


class VaultEntryDetailView(VaultDashboardAccessMixin, VaultPageContextMixin, DetailView):
    model = VaultEntry
    template_name = "vault/entry_detail.html"
    context_object_name = "entry"
    page_title = "Entry details"

    def get_queryset(self):
        return VaultEntry.objects.filter(tenant=self.request.hrm_tenant).select_related(
            "category", "category__customer", "project"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["attachment_form"] = VaultFileAttachmentForm()
        ctx["share_form"] = VaultShareForm()
        entry = self.object
        # Legacy: ?show_password=1 still enables reveal for this entry (merged into session).
        if self.request.GET.get("show_password") == "1":
            _vault_session_mark_revealed(request=self.request, entry_pk=entry.pk)

        revealed_ids = self.request.session.get("vault_pw_reveal_ids", [])
        password_reveal_active = entry.pk in revealed_ids
        revealed = ""
        if password_reveal_active:
            revealed = entry.get_password()
        ctx["password_reveal_active"] = password_reveal_active
        ctx["revealed_password"] = revealed
        ctx["password_missing"] = password_reveal_active and not entry.password_encrypted
        ctx["password_reveal_unreadable"] = (
            password_reveal_active and bool(entry.password_encrypted) and not revealed
        )
        ctx["entry_copy_payload"] = {
            "name": entry.name,
            "customer": entry.category.customer.name if entry.category.customer_id else "",
            "project": entry.project.key if entry.project_id else "",
            "url": entry.url or "",
            "username": entry.username or "",
            "password": revealed,
            "notes": entry.notes or "",
        }
        return ctx


def _vault_session_mark_revealed(*, request, entry_pk: int) -> None:
    ids = list(request.session.get("vault_pw_reveal_ids", []))
    if entry_pk not in ids:
        ids.append(entry_pk)
        request.session["vault_pw_reveal_ids"] = ids
        request.session.modified = True


class VaultEntryRevealPasswordView(VaultDashboardAccessMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        entry = get_object_or_404(VaultEntry, tenant=request.hrm_tenant, pk=kwargs["pk"])
        _vault_session_mark_revealed(request=request, entry_pk=entry.pk)
        messages.success(request, "Password is shown below. Click Hide when you are done.")
        return redirect("vault:entry_detail", pk=entry.pk)


class VaultEntryHidePasswordView(VaultDashboardAccessMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        entry = get_object_or_404(VaultEntry, tenant=request.hrm_tenant, pk=kwargs["pk"])
        ids = [i for i in request.session.get("vault_pw_reveal_ids", []) if i != entry.pk]
        request.session["vault_pw_reveal_ids"] = ids
        request.session.modified = True
        return redirect("vault:entry_detail", pk=entry.pk)


class VaultEntryAttachmentCreateView(VaultAdminMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        entry = get_object_or_404(VaultEntry, tenant=request.hrm_tenant, pk=kwargs["pk"])
        form = VaultFileAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.entry = entry
            attachment.tenant = request.hrm_tenant
            attachment.save()
            messages.success(request, "Attachment uploaded.")
        else:
            messages.error(request, "Could not upload attachment.")
        return redirect("vault:entry_detail", pk=entry.pk)


class VaultEntryShareCreateView(VaultDashboardAccessMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        entry = get_object_or_404(VaultEntry, tenant=request.hrm_tenant, pk=kwargs["pk"])
        form = VaultShareForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Could not share entry. Check the form fields.")
            return redirect("vault:entry_detail", pk=entry.pk)

        data = form.cleaned_data
        email = (data["shared_with_email"] or "").strip().lower()
        share, _created = VaultSharedEntry.objects.update_or_create(
            tenant=request.hrm_tenant,
            entry=entry,
            shared_with_email=email,
            defaults={
                "permission": data["permission"],
                "expires_at": data["expires_at"],
                "is_active": data["is_active"],
                "shared_by": request.user,
            },
        )
        ok, err = send_vault_share_invite_email(request, share)
        if ok:
            messages.success(
                request,
                f"Invite saved and an email with a secure link was sent to {share.shared_with_email}.",
            )
        else:
            messages.warning(
                request,
                "Invite saved, but the email could not be sent. "
                "Confirm EMAIL_* and DEFAULT_FROM_EMAIL in .env. "
                f"Error: {err or 'unknown'}",
            )
        return redirect("vault:entry_detail", pk=entry.pk)


class VaultSharedEntryPublicView(TemplateView):
    """
    Unauthenticated page: recipient opens signed link from email to view credentials.
    """

    template_name = "vault/shared_public.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        token = (self.request.GET.get("t") or "").strip()
        if not token:
            raise Http404("Missing link token.")
        try:
            share_pk = vault_share_parse_token(token)
        except (BadSignature, SignatureExpired):
            raise Http404("This link is invalid or has expired.")

        share = (
            VaultSharedEntry.objects.select_related(
                "tenant",
                "entry",
                "entry__category",
                "entry__category__customer",
                "entry__project",
            )
            .filter(pk=share_pk)
            .first()
        )
        if share is None or not share_record_is_usable(share):
            raise Http404("This share is no longer available.")

        entry = share.entry
        password_plain = entry.get_password()
        customer_name = ""
        if entry.category_id and entry.category.customer_id:
            customer_name = entry.category.customer.name
        project_label = entry.project.key if entry.project_id else ""

        ctx["share"] = share
        ctx["entry"] = entry
        ctx["tenant_name"] = share.tenant.name if share.tenant_id else ""
        ctx["customer_name"] = customer_name or "—"
        ctx["project_label"] = project_label or "—"
        ctx["password_plain"] = password_plain
        ctx["permission_display"] = share.get_permission_display()
        ctx["share_permission"] = share.permission
        ctx["copy_payload"] = {
            "name": entry.name,
            "customer": customer_name,
            "project": project_label,
            "url": entry.url or "",
            "username": entry.username or "",
            "password": password_plain,
            "notes": entry.notes or "",
        }
        return ctx

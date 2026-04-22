from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from .forms import PaymentForm, PropertyForm, RentalAgreementForm, RentalTenantForm
from .mixins import RentalAdminMixin, RentalDashboardAccessMixin, RentalPageContextMixin
from .models import DuePayment, Payment, Property, RentalAgreement, RentalTenant, SMSLog


class RentalDashboardView(RentalDashboardAccessMixin, RentalPageContextMixin, TemplateView):
    template_name = "rental_management/dashboard.html"
    page_title = "Rental Management"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = self.request.hrm_tenant
        ctx["property_n"] = Property.objects.filter(tenant=tenant).count()
        ctx["vacant_n"] = Property.objects.filter(tenant=tenant, status="VACANT").count()
        ctx["tenant_n"] = RentalTenant.objects.filter(tenant=tenant, is_active=True).count()
        ctx["agreement_n"] = RentalAgreement.objects.filter(tenant=tenant, status="ACTIVE").count()
        ctx["due_amount"] = DuePayment.objects.filter(tenant=tenant, is_paid=False).aggregate(v=Sum("due_amount"))["v"] or 0
        ctx["recent_payments"] = (
            Payment.objects.filter(tenant=tenant)
            .select_related("agreement", "agreement__rental_tenant", "agreement__property")
            .order_by("-payment_date", "-id")[:5]
        )
        return ctx


class RentalGuideView(RentalAdminMixin, RentalPageContextMixin, TemplateView):
    template_name = "rental_management/rental_guide_bn.html"
    page_title = "Rental guide (Bangla)"
    permission_codename = "rental.view"


class PropertyListView(RentalAdminMixin, RentalPageContextMixin, ListView):
    model = Property
    template_name = "rental_management/property_list.html"
    context_object_name = "rows"
    page_title = "Properties"
    permission_codename = "rental.view_property"
    paginate_by = 20

    def get_queryset(self):
        qs = Property.objects.filter(tenant=self.request.hrm_tenant).select_related("current_tenant")
        q = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()
        ptype = (self.request.GET.get("property_type") or "").strip()
        if q:
            qs = qs.filter(property_number__icontains=q)
        if status:
            qs = qs.filter(status=status)
        if ptype:
            qs = qs.filter(property_type=ptype)
        return qs.order_by("property_type", "property_number")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["qs_no_page"] = params.urlencode()
        ctx["status_choices"] = Property.STATUS_CHOICES
        ctx["type_choices"] = Property.PROPERTY_TYPES
        ctx["selected"] = {
            "q": self.request.GET.get("q", ""),
            "status": self.request.GET.get("status", ""),
            "property_type": self.request.GET.get("property_type", ""),
        }
        return ctx


class PropertyCreateView(RentalAdminMixin, RentalPageContextMixin, View):
    page_title = "Add property"
    permission_codename = "rental.add_property"

    def get(self, request):
        return render(
            request,
            "rental_management/property_form.html",
            {"form": PropertyForm(), "is_edit": False, "active_page": "rental", "page_title": self.page_title},
        )

    def post(self, request):
        form = PropertyForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = request.hrm_tenant
            obj.created_by = request.user
            obj.save()
            messages.success(request, "Property created.")
            return redirect("rental_management:property_list")
        return render(
            request,
            "rental_management/property_form.html",
            {"form": form, "is_edit": False, "active_page": "rental", "page_title": self.page_title},
        )


class PropertyUpdateView(RentalAdminMixin, RentalPageContextMixin, View):
    page_title = "Edit property"
    permission_codename = "rental.change_property"

    def get_object(self, request, pk):
        return get_object_or_404(Property, tenant=request.hrm_tenant, pk=pk)

    def get(self, request, pk):
        obj = self.get_object(request, pk)
        return render(
            request,
            "rental_management/property_form.html",
            {"form": PropertyForm(instance=obj), "object": obj, "is_edit": True, "active_page": "rental", "page_title": self.page_title},
        )

    def post(self, request, pk):
        obj = self.get_object(request, pk)
        form = PropertyForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Property updated.")
            return redirect("rental_management:property_list")
        return render(
            request,
            "rental_management/property_form.html",
            {"form": form, "object": obj, "is_edit": True, "active_page": "rental", "page_title": self.page_title},
        )


class PropertyDetailView(RentalAdminMixin, RentalPageContextMixin, DetailView):
    model = Property
    template_name = "rental_management/property_detail.html"
    context_object_name = "object"
    page_title = "Property details"
    permission_codename = "rental.view_property"

    def get_queryset(self):
        return Property.objects.filter(tenant=self.request.hrm_tenant).select_related("current_tenant")


class RentalTenantListView(RentalAdminMixin, RentalPageContextMixin, ListView):
    model = RentalTenant
    template_name = "rental_management/tenant_list.html"
    context_object_name = "rows"
    page_title = "Tenants"
    permission_codename = "rental.view_tenant"
    paginate_by = 20

    def get_queryset(self):
        qs = RentalTenant.objects.filter(tenant=self.request.hrm_tenant)
        q = (self.request.GET.get("q") or "").strip()
        active = (self.request.GET.get("active") or "").strip().lower()
        if q:
            qs = qs.filter(name__icontains=q)
        if active == "yes":
            qs = qs.filter(is_active=True)
        elif active == "no":
            qs = qs.filter(is_active=False)
        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["qs_no_page"] = params.urlencode()
        ctx["selected"] = {
            "q": self.request.GET.get("q", ""),
            "active": self.request.GET.get("active", ""),
        }
        return ctx


class RentalTenantCreateView(RentalAdminMixin, RentalPageContextMixin, View):
    page_title = "Add tenant"
    permission_codename = "rental.add_tenant"

    def get(self, request):
        return render(
            request,
            "rental_management/tenant_form.html",
            {"form": RentalTenantForm(), "is_edit": False, "active_page": "rental", "page_title": self.page_title},
        )

    def post(self, request):
        form = RentalTenantForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = request.hrm_tenant
            obj.created_by = request.user
            obj.save()
            messages.success(request, "Tenant created.")
            return redirect("rental_management:tenant_list")
        return render(
            request,
            "rental_management/tenant_form.html",
            {"form": form, "is_edit": False, "active_page": "rental", "page_title": self.page_title},
        )


class RentalTenantUpdateView(RentalAdminMixin, RentalPageContextMixin, View):
    page_title = "Edit tenant"
    permission_codename = "rental.change_tenant"

    def get_object(self, request, pk):
        return get_object_or_404(RentalTenant, tenant=request.hrm_tenant, pk=pk)

    def get(self, request, pk):
        obj = self.get_object(request, pk)
        return render(
            request,
            "rental_management/tenant_form.html",
            {"form": RentalTenantForm(instance=obj), "object": obj, "is_edit": True, "active_page": "rental", "page_title": self.page_title},
        )

    def post(self, request, pk):
        obj = self.get_object(request, pk)
        form = RentalTenantForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Tenant updated.")
            return redirect("rental_management:tenant_list")
        return render(
            request,
            "rental_management/tenant_form.html",
            {"form": form, "object": obj, "is_edit": True, "active_page": "rental", "page_title": self.page_title},
        )


class RentalTenantDetailView(RentalAdminMixin, RentalPageContextMixin, DetailView):
    model = RentalTenant
    template_name = "rental_management/tenant_detail.html"
    context_object_name = "object"
    page_title = "Tenant details"
    permission_codename = "rental.view_tenant"

    def get_queryset(self):
        return RentalTenant.objects.filter(tenant=self.request.hrm_tenant).prefetch_related("agreements")


class RentalAgreementListView(RentalAdminMixin, RentalPageContextMixin, ListView):
    model = RentalAgreement
    template_name = "rental_management/agreement_list.html"
    context_object_name = "rows"
    page_title = "Agreements"
    permission_codename = "rental.view_agreement"
    paginate_by = 20

    def get_queryset(self):
        qs = RentalAgreement.objects.filter(tenant=self.request.hrm_tenant).select_related("property", "rental_tenant")
        status = (self.request.GET.get("status") or "").strip()
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-start_date", "-id")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = self.request.GET.copy()
        params.pop("page", None)
        ctx["qs_no_page"] = params.urlencode()
        ctx["status_choices"] = RentalAgreement.STATUS_CHOICES
        ctx["selected"] = {"status": self.request.GET.get("status", "")}
        return ctx


class RentalAgreementCreateView(RentalAdminMixin, RentalPageContextMixin, View):
    page_title = "Add agreement"
    permission_codename = "rental.add_agreement"

    def get(self, request):
        return render(
            request,
            "rental_management/agreement_form.html",
            {"form": RentalAgreementForm(tenant=request.hrm_tenant), "is_edit": False, "active_page": "rental", "page_title": self.page_title},
        )

    def post(self, request):
        form = RentalAgreementForm(request.POST, request.FILES, tenant=request.hrm_tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = request.hrm_tenant
            obj.created_by = request.user
            obj.save()
            obj.property.status = "OCCUPIED"
            obj.property.current_tenant = obj.rental_tenant
            obj.property.save(update_fields=["status", "current_tenant"])
            messages.success(request, "Agreement created.")
            return redirect("rental_management:agreement_list")
        return render(
            request,
            "rental_management/agreement_form.html",
            {"form": form, "is_edit": False, "active_page": "rental", "page_title": self.page_title},
        )


class RentalAgreementUpdateView(RentalAdminMixin, RentalPageContextMixin, View):
    page_title = "Edit agreement"
    permission_codename = "rental.change_agreement"

    def get_object(self, request, pk):
        return get_object_or_404(RentalAgreement, tenant=request.hrm_tenant, pk=pk)

    def get(self, request, pk):
        obj = self.get_object(request, pk)
        return render(
            request,
            "rental_management/agreement_form.html",
            {
                "form": RentalAgreementForm(instance=obj, tenant=request.hrm_tenant),
                "object": obj,
                "is_edit": True,
                "active_page": "rental",
                "page_title": self.page_title,
            },
        )

    def post(self, request, pk):
        obj = self.get_object(request, pk)
        form = RentalAgreementForm(request.POST, request.FILES, instance=obj, tenant=request.hrm_tenant)
        if form.is_valid():
            form.save()
            messages.success(request, "Agreement updated.")
            return redirect("rental_management:agreement_list")
        return render(
            request,
            "rental_management/agreement_form.html",
            {"form": form, "object": obj, "is_edit": True, "active_page": "rental", "page_title": self.page_title},
        )


class RentalAgreementDetailView(RentalAdminMixin, RentalPageContextMixin, DetailView):
    model = RentalAgreement
    template_name = "rental_management/agreement_detail.html"
    context_object_name = "object"
    page_title = "Agreement details"
    permission_codename = "rental.view_agreement"

    def get_queryset(self):
        return RentalAgreement.objects.filter(tenant=self.request.hrm_tenant).select_related("property", "rental_tenant")


class RentalAgreementTerminateView(RentalAdminMixin, View):
    permission_codename = "rental.change_agreement"

    def post(self, request, pk):
        obj = get_object_or_404(RentalAgreement, tenant=request.hrm_tenant, pk=pk)
        obj.status = "TERMINATED"
        obj.save(update_fields=["status", "updated_at"])
        obj.property.status = "VACANT"
        obj.property.current_tenant = None
        obj.property.save(update_fields=["status", "current_tenant", "updated_at"])
        messages.success(request, "Agreement terminated.")
        return redirect("rental_management:agreement_detail", pk=pk)


class PaymentListView(RentalAdminMixin, RentalPageContextMixin, ListView):
    model = Payment
    template_name = "rental_management/payment_list.html"
    context_object_name = "rows"
    page_title = "Payments"
    permission_codename = "rental.view_payment"
    paginate_by = 20

    def get_queryset(self):
        return (
            Payment.objects.filter(tenant=self.request.hrm_tenant)
            .select_related("agreement", "agreement__rental_tenant", "agreement__property")
            .order_by("-payment_date", "-id")
        )


class PaymentCreateView(RentalAdminMixin, RentalPageContextMixin, View):
    page_title = "Record payment"
    permission_codename = "rental.add_payment"

    def get(self, request):
        return render(
            request,
            "rental_management/payment_form.html",
            {"form": PaymentForm(tenant=request.hrm_tenant), "is_edit": False, "active_page": "rental", "page_title": self.page_title},
        )

    def post(self, request):
        form = PaymentForm(request.POST, tenant=request.hrm_tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.tenant = request.hrm_tenant
            obj.created_by = request.user
            obj.save()
            messages.success(request, "Payment recorded.")
            return redirect("rental_management:payment_list")
        return render(
            request,
            "rental_management/payment_form.html",
            {"form": form, "is_edit": False, "active_page": "rental", "page_title": self.page_title},
        )


class PaymentDetailView(RentalAdminMixin, RentalPageContextMixin, DetailView):
    model = Payment
    template_name = "rental_management/payment_detail.html"
    context_object_name = "object"
    page_title = "Payment details"
    permission_codename = "rental.view_payment"

    def get_queryset(self):
        return Payment.objects.filter(tenant=self.request.hrm_tenant).select_related(
            "agreement",
            "agreement__rental_tenant",
            "agreement__property",
        )


class DuePaymentListView(RentalAdminMixin, RentalPageContextMixin, ListView):
    model = DuePayment
    template_name = "rental_management/due_list.html"
    context_object_name = "rows"
    page_title = "Due payments"
    permission_codename = "rental.view_payment"
    paginate_by = 20

    def get_queryset(self):
        return (
            DuePayment.objects.filter(tenant=self.request.hrm_tenant)
            .select_related("agreement", "agreement__rental_tenant", "agreement__property")
            .order_by("-due_month", "-id")
        )


class SMSLogListView(RentalAdminMixin, RentalPageContextMixin, ListView):
    model = SMSLog
    template_name = "rental_management/sms_log_list.html"
    context_object_name = "rows"
    page_title = "SMS logs"
    permission_codename = "rental.send_sms"
    paginate_by = 20

    def get_queryset(self):
        return SMSLog.objects.filter(tenant=self.request.hrm_tenant).select_related("rental_tenant").order_by("-created_at")

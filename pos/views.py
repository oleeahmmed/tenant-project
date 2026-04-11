import json
from decimal import Decimal

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from foundation.models import Customer, PaymentMethod, Warehouse
from hrm.tenant_scope import get_hrm_tenant

from .forms import CloseSessionForm, OpenSessionForm, POSRegisterForm
from .mixins import POSAdminMixin, POSDashboardAccessMixin, POSPageContextMixin
from .models import POSRegister, POSPayment, POSSale, POSSession
from .services.checkout import create_sale_from_checkout

SESSION_POS_KEY = "pos_session_id"


def _cash_expected_for_session(session: POSSession) -> Decimal:
    total = session.opening_cash or Decimal("0")
    for sale in session.sales.filter(status=POSSale.Status.COMPLETED).prefetch_related("payments__payment_method"):
        for p in sale.payments.all():
            if "cash" in (p.payment_method.code or "").lower():
                total += p.amount or Decimal("0")
    return total


class POSDashboardView(POSDashboardAccessMixin, POSPageContextMixin, TemplateView):
    template_name = "pos/dashboard.html"
    page_title = "POS"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        t = self.request.hrm_tenant
        today = timezone.now().date()
        qs = POSSale.objects.filter(tenant=t, status=POSSale.Status.COMPLETED, sale_datetime__date=today)
        ctx["today_total"] = qs.aggregate(s=Sum("total_amount"))["s"] or Decimal("0")
        ctx["today_count"] = qs.count()
        ctx["registers"] = POSRegister.objects.filter(tenant=t, is_active=True).order_by("code")
        ctx["open_sessions"] = POSSession.objects.filter(
            register__tenant=t, status=POSSession.Status.OPEN
        ).select_related("register", "opened_by")
        sid = self.request.session.get(SESSION_POS_KEY)
        ctx["my_session_id"] = sid
        return ctx


class POSGuideView(POSDashboardAccessMixin, POSPageContextMixin, TemplateView):
    template_name = "pos/pos_guide_bn.html"
    page_title = "POS guide (Bangla)"


class POSRegisterListView(POSDashboardAccessMixin, POSPageContextMixin, ListView):
    model = POSRegister
    template_name = "pos/register_list.html"
    context_object_name = "registers"
    page_title = "Registers"

    def get_queryset(self):
        return POSRegister.objects.filter(tenant=self.request.hrm_tenant).select_related("default_warehouse").order_by(
            "code"
        )


class POSRegisterCreateView(POSAdminMixin, POSPageContextMixin, CreateView):
    model = POSRegister
    form_class = POSRegisterForm
    template_name = "pos/register_form.html"
    success_url = reverse_lazy("pos:register_list")
    page_title = "Add register"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.save()
        messages.success(self.request, "Register saved.")
        return redirect(self.success_url)


class POSRegisterUpdateView(POSAdminMixin, POSPageContextMixin, UpdateView):
    model = POSRegister
    form_class = POSRegisterForm
    template_name = "pos/register_form.html"
    context_object_name = "register"
    page_title = "Edit register"
    success_url = reverse_lazy("pos:register_list")

    def get_queryset(self):
        return POSRegister.objects.filter(tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Register updated.")
        return super().form_valid(form)


class OpenSessionView(POSAdminMixin, POSPageContextMixin, TemplateView):
    template_name = "pos/open_session.html"
    page_title = "Open POS session"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = OpenSessionForm(tenant=self.request.hrm_tenant)
        return ctx

    def post(self, request, *args, **kwargs):
        form = OpenSessionForm(request.POST, tenant=request.hrm_tenant)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "page_title": self.page_title})
        register = form.cleaned_data["register"]
        if POSSession.objects.filter(register=register, status=POSSession.Status.OPEN).exists():
            messages.error(request, "This register already has an open session. Close it first.")
            return redirect("pos:session_list")
        session = POSSession.objects.create(
            register=register,
            opened_by=request.user,
            opening_cash=form.cleaned_data["opening_cash"],
            status=POSSession.Status.OPEN,
        )
        request.session[SESSION_POS_KEY] = session.pk
        messages.success(request, f"Session opened for {register.code}.")
        return redirect("pos:cashier")


class CloseSessionView(POSAdminMixin, POSPageContextMixin, TemplateView):
    template_name = "pos/close_session.html"
    page_title = "Close POS session"

    def get_session(self):
        sid = self.request.session.get(SESSION_POS_KEY)
        if not sid:
            return None
        return get_object_or_404(
            POSSession.objects.filter(register__tenant=self.request.hrm_tenant, status=POSSession.Status.OPEN),
            pk=sid,
        )

    def get(self, request, *args, **kwargs):
        session = self.get_session()
        if not session:
            messages.warning(request, "No open session.")
            return redirect("pos:dashboard")
        expected = _cash_expected_for_session(session)
        form = CloseSessionForm()
        return render(
            request,
            self.template_name,
            {
                "session": session,
                "expected_cash": expected,
                "form": form,
                "page_title": self.page_title,
            },
        )

    def post(self, request, *args, **kwargs):
        session = self.get_session()
        if not session:
            return redirect("pos:dashboard")
        form = CloseSessionForm(request.POST)
        expected = _cash_expected_for_session(session)
        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"session": session, "expected_cash": expected, "form": form, "page_title": self.page_title},
            )
        closing = form.cleaned_data["closing_cash"]
        diff = closing - expected
        session.closed_at = timezone.now()
        session.closed_by = request.user
        session.closing_cash = closing
        session.expected_cash = expected
        session.cash_difference = diff
        session.status = POSSession.Status.CLOSED
        session.notes = form.cleaned_data.get("notes") or ""
        session.save()
        if SESSION_POS_KEY in request.session:
            del request.session[SESSION_POS_KEY]
        messages.success(request, "Session closed.")
        return redirect("pos:dashboard")


class CashierView(POSAdminMixin, POSPageContextMixin, TemplateView):
    template_name = "pos/cashier.html"
    page_title = "Cashier"

    def dispatch(self, request, *args, **kwargs):
        # Must run before using request.hrm_tenant; this view's dispatch runs before
        # FoundationAdminMixin.dispatch (super()) attaches the tenant.
        request.hrm_tenant = get_hrm_tenant(request)
        sid = request.session.get(SESSION_POS_KEY)
        if not sid:
            messages.warning(request, "Open a POS session first.")
            return redirect("pos:open_session")
        session = POSSession.objects.filter(
            pk=sid, register__tenant=request.hrm_tenant, status=POSSession.Status.OPEN
        ).select_related("register", "register__default_warehouse").first()
        if not session:
            if SESSION_POS_KEY in request.session:
                del request.session[SESSION_POS_KEY]
            messages.error(request, "Session is no longer valid.")
            return redirect("pos:dashboard")
        self.pos_session = session
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        t = self.request.hrm_tenant
        session = self.pos_session
        reg = session.register
        ctx["pos_session"] = session
        ctx["register"] = reg
        ctx["warehouse"] = reg.default_warehouse
        ctx["payment_methods"] = PaymentMethod.objects.filter(tenant=t, is_active=True).order_by("name")
        ctx["customers"] = Customer.objects.filter(tenant=t, is_active=True).order_by("name")[:200]
        return ctx


class CheckoutView(POSAdminMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        sid = request.session.get(SESSION_POS_KEY)
        if not sid:
            return JsonResponse({"ok": False, "error": "No POS session."}, status=400)
        session = POSSession.objects.filter(
            pk=sid, register__tenant=request.hrm_tenant, status=POSSession.Status.OPEN
        ).select_related("register__default_warehouse").first()
        if not session:
            return JsonResponse({"ok": False, "error": "Invalid session."}, status=400)

        try:
            body = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"ok": False, "error": "Invalid JSON."}, status=400)

        tenant = request.hrm_tenant
        warehouse = session.register.default_warehouse

        try:
            sale = create_sale_from_checkout(
                tenant=tenant,
                session=session,
                user=request.user,
                warehouse=warehouse,
                lines_payload=body.get("lines") or [],
                payments_payload=body.get("payments") or [],
                customer_id=body.get("customer_id"),
                tax_amount=body.get("tax_amount"),
                discount_amount=body.get("discount_amount"),
                notes=body.get("notes") or "",
            )
        except ValidationError as e:
            parts = []
            if hasattr(e, "error_dict") and e.error_dict:
                for k, v in e.error_dict.items():
                    parts.append(f"{k}: {v}")
            elif getattr(e, "messages", None):
                parts.extend(e.messages)
            else:
                parts.append(str(e))
            return JsonResponse({"ok": False, "error": "; ".join(parts)}, status=400)

        return JsonResponse(
            {
                "ok": True,
                "doc_no": sale.doc_no,
                "sale_id": sale.pk,
                "redirect": reverse("pos:sale_receipt", kwargs={"pk": sale.pk}),
            }
        )


class POSSaleListView(POSDashboardAccessMixin, POSPageContextMixin, ListView):
    model = POSSale
    template_name = "pos/sale_list.html"
    context_object_name = "sales"
    paginate_by = 25
    page_title = "POS sales"

    def get_queryset(self):
        qs = (
            POSSale.objects.filter(tenant=self.request.hrm_tenant)
            .select_related("session__register", "customer", "created_by")
            .order_by("-sale_datetime")
        )
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(doc_no__icontains=q)
        return qs


class POSSaleDetailView(POSDashboardAccessMixin, POSPageContextMixin, DetailView):
    model = POSSale
    template_name = "pos/sale_detail.html"
    context_object_name = "sale"
    page_title = "Sale"

    def get_queryset(self):
        return (
            POSSale.objects.filter(tenant=self.request.hrm_tenant)
            .select_related("session__register", "customer", "warehouse", "created_by")
            .prefetch_related("lines__product", "payments__payment_method")
        )


class SaleReceiptPrintView(POSDashboardAccessMixin, POSPageContextMixin, DetailView):
    model = POSSale
    template_name = "pos/receipt_print.html"
    context_object_name = "sale"

    def get_queryset(self):
        return (
            POSSale.objects.filter(tenant=self.request.hrm_tenant)
            .select_related("tenant", "session__register", "customer", "warehouse", "created_by")
            .prefetch_related("lines__product", "payments__payment_method")
        )


class POSSessionListView(POSDashboardAccessMixin, POSPageContextMixin, ListView):
    model = POSSession
    template_name = "pos/session_list.html"
    context_object_name = "sessions"
    paginate_by = 30
    page_title = "POS sessions"

    def get_queryset(self):
        return (
            POSSession.objects.filter(register__tenant=self.request.hrm_tenant)
            .select_related("register", "opened_by", "closed_by")
            .order_by("-opened_at")
        )


class VoidSaleView(POSAdminMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        sale = get_object_or_404(POSSale, pk=pk, tenant=request.hrm_tenant)
        if sale.status != POSSale.Status.COMPLETED:
            messages.error(request, "Only completed sales can be voided.")
            return redirect("pos:sale_detail", pk=pk)
        sale.status = POSSale.Status.VOID
        sale.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Sale {sale.doc_no} voided.")
        return redirect("pos:sale_detail", pk=pk)

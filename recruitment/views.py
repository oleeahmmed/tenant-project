from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from hrm.mixins import HrmAdminMixin, HrmPageContextMixin, PostOnlyMixin

from .forms import ApplicationForm, ApplicationQuickCreateForm, JobPostingForm
from .models import Application, JobPosting


class RecruitmentPageMixin(HrmPageContextMixin):
    """Same shell nav as HRM; resolver url_name starts with recruitment_."""

    active_page = "hrm"


# ── Job postings ──────────────────────────────────────────────────────────────


class JobPostingListView(HrmAdminMixin, RecruitmentPageMixin, ListView):
    model = JobPosting
    template_name = "recruitment/job_list.html"
    context_object_name = "jobs"
    page_title = "Recruitment · Jobs"

    def get_queryset(self):
        return (
            JobPosting.objects.filter(tenant=self.request.hrm_tenant)
            .select_related("department", "created_by")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = JobPostingForm(tenant=self.request.hrm_tenant)
        return ctx


class JobPostingCreateView(HrmAdminMixin, PostOnlyMixin, CreateView):
    model = JobPosting
    form_class = JobPostingForm
    success_url = reverse_lazy("hrm:recruitment_job_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        kwargs.setdefault("data", self.request.POST)
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.tenant = self.request.hrm_tenant
        self.object.created_by = self.request.user
        self.object.save()
        messages.success(self.request, "Job posting created.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the job form errors.")
        return redirect(self.success_url)


class JobPostingUpdateView(HrmAdminMixin, RecruitmentPageMixin, UpdateView):
    model = JobPosting
    form_class = JobPostingForm
    template_name = "recruitment/job_edit.html"
    context_object_name = "job"
    success_url = reverse_lazy("hrm:recruitment_job_list")
    page_title = "Edit job posting"

    def get_queryset(self):
        return JobPosting.objects.filter(tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Job posting updated.")
        return super().form_valid(form)


class JobPostingDeleteView(HrmAdminMixin, PostOnlyMixin, DeleteView):
    model = JobPosting
    success_url = reverse_lazy("hrm:recruitment_job_list")

    def get_queryset(self):
        return JobPosting.objects.filter(tenant=self.request.hrm_tenant)

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        title = self.object.title
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, f"Job “{title}” removed.")
        return response


# ── Applications ──────────────────────────────────────────────────────────────


class ApplicationListView(HrmAdminMixin, RecruitmentPageMixin, ListView):
    model = Application
    template_name = "recruitment/application_list.html"
    context_object_name = "applications"
    page_title = "Recruitment · Applications"

    def get_queryset(self):
        qs = Application.objects.filter(job__tenant=self.request.hrm_tenant).select_related(
            "job", "job__department", "hired_employee"
        )
        job_id = self.request.GET.get("job")
        stage = self.request.GET.get("stage")
        if job_id and str(job_id).isdigit():
            qs = qs.filter(job_id=int(job_id))
        if stage and stage in {c.value for c in Application.Stage}:
            qs = qs.filter(stage=stage)
        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = self.request.hrm_tenant
        ctx["jobs_filter"] = JobPosting.objects.filter(tenant=tenant).order_by("-created_at")
        ctx["filter_job"] = self.request.GET.get("job") or ""
        ctx["filter_stage"] = self.request.GET.get("stage") or ""
        ctx["quick_form"] = ApplicationQuickCreateForm()
        ctx["job_postings"] = JobPosting.objects.filter(tenant=tenant).order_by("-created_at")[:200]
        return ctx


class ApplicationCreateView(HrmAdminMixin, View):
    """POST from application list — requires job pk in POST."""

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        job_id = request.POST.get("job")
        if not job_id or not str(job_id).isdigit():
            messages.error(request, "Select a job posting.")
            return redirect("hrm:recruitment_application_list")
        job = get_object_or_404(
            JobPosting.objects.filter(tenant=request.hrm_tenant),
            pk=int(job_id),
        )
        form = ApplicationQuickCreateForm(request.POST, request.FILES)
        if form.is_valid():
            app = form.save(commit=False)
            app.job = job
            try:
                app.save()
                messages.success(request, "Application added.")
            except IntegrityError:
                messages.error(
                    request,
                    "This email already has an application for this job.",
                )
        else:
            messages.error(request, "Please fix the application form.")
        return redirect("hrm:recruitment_application_list")


class ApplicationUpdateView(HrmAdminMixin, RecruitmentPageMixin, UpdateView):
    model = Application
    form_class = ApplicationForm
    template_name = "recruitment/application_edit.html"
    context_object_name = "application"
    success_url = reverse_lazy("hrm:recruitment_application_list")
    page_title = "Application"

    def get_queryset(self):
        return Application.objects.filter(job__tenant=self.request.hrm_tenant)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["tenant"] = self.request.hrm_tenant
        return kwargs

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.reviewed_by = self.request.user
        obj.reviewed_at = timezone.now()
        obj.save()
        messages.success(self.request, "Application updated.")
        return redirect(self.success_url)


class ApplicationDeleteView(HrmAdminMixin, PostOnlyMixin, DeleteView):
    model = Application
    success_url = reverse_lazy("hrm:recruitment_application_list")

    def get_queryset(self):
        return Application.objects.filter(job__tenant=self.request.hrm_tenant)

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, "Application removed.")
        return response


# Aliases (hrm namespace via include)
recruitment_job_list = JobPostingListView.as_view()
recruitment_job_create = JobPostingCreateView.as_view()
recruitment_job_edit = JobPostingUpdateView.as_view()
recruitment_job_delete = JobPostingDeleteView.as_view()
recruitment_application_list = ApplicationListView.as_view()
recruitment_application_create = ApplicationCreateView.as_view()
recruitment_application_edit = ApplicationUpdateView.as_view()
recruitment_application_delete = ApplicationDeleteView.as_view()

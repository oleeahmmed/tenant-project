from django.contrib import messages
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView, TemplateView

from .forms import StaffForm, StudentForm
from .mixins import SchoolAdminMixin, SchoolPageContextMixin
from .models import (
    AcademicYear,
    Exam,
    FeeCategory,
    FeeCollection,
    FeeDiscount,
    FeeStructure,
    SchoolClass,
    Section,
    SMSLog,
    Staff,
    StaffAttendance,
    Student,
    StudentAttendance,
    Subject,
)


class SchoolDashboardView(SchoolAdminMixin, SchoolPageContextMixin, TemplateView):
    template_name = "school/dashboard.html"
    page_title = "School Management"
    permission_codename = "school.view_reports"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tenant = self.request.hrm_tenant
        ctx["students_n"] = Student.objects.filter(tenant=tenant, status=Student.Status.ACTIVE).count()
        ctx["staff_n"] = Staff.objects.filter(tenant=tenant, status=Staff.Status.ACTIVE).count()
        ctx["attendance_present_n"] = StudentAttendance.objects.filter(
            tenant=tenant, status=StudentAttendance.Status.PRESENT
        ).count()
        ctx["attendance_absent_n"] = StudentAttendance.objects.filter(
            tenant=tenant, status=StudentAttendance.Status.ABSENT
        ).count()
        ctx["fees_collected"] = (
            FeeCollection.objects.filter(tenant=tenant, status=FeeCollection.Status.PAID).aggregate(v=models.Sum("amount_paid"))["v"]
            or 0
        )
        ctx["fees_due"] = (
            FeeCollection.objects.filter(tenant=tenant)
            .exclude(status=FeeCollection.Status.PAID)
            .aggregate(v=models.Sum("amount_due"))["v"]
            or 0
        )
        ctx["upcoming_exams"] = Exam.objects.filter(tenant=tenant).order_by("start_date")[:6]
        return ctx


class SchoolGuideView(SchoolAdminMixin, SchoolPageContextMixin, TemplateView):
    template_name = "school/school_guide_bn.html"
    page_title = "School guide (Bangla)"
    permission_codename = "school.view"


class StudentListView(SchoolAdminMixin, SchoolPageContextMixin, ListView):
    template_name = "school/student_list.html"
    context_object_name = "rows"
    paginate_by = 30
    page_title = "Students"
    permission_codename = "school.view_student"

    def get_queryset(self):
        qs = Student.objects.filter(tenant=self.request.hrm_tenant).select_related("current_class", "current_section")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(name__icontains=q)
        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["selected"] = {"q": self.request.GET.get("q", "")}
        return ctx


class StudentCreateView(SchoolAdminMixin, SchoolPageContextMixin, View):
    page_title = "Add student"
    permission_codename = "school.manage"

    def get(self, request):
        return render(
            request,
            "school/student_form.html",
            {
                "form": StudentForm(tenant=request.hrm_tenant),
                "is_edit": False,
                "active_page": "school",
                "page_title": self.page_title,
            },
        )

    def post(self, request):
        form = StudentForm(request.POST, request.FILES, tenant=request.hrm_tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            messages.success(request, "Student saved.")
            return redirect("school:student_list")
        return render(
            request,
            "school/student_form.html",
            {"form": form, "is_edit": False, "active_page": "school", "page_title": self.page_title},
        )


class StudentUpdateView(SchoolAdminMixin, SchoolPageContextMixin, View):
    page_title = "Edit student"
    permission_codename = "school.manage"

    def get_object(self, request, pk):
        return get_object_or_404(Student, tenant=request.hrm_tenant, pk=pk)

    def get(self, request, pk):
        obj = self.get_object(request, pk)
        return render(
            request,
            "school/student_form.html",
            {
                "form": StudentForm(instance=obj, tenant=request.hrm_tenant),
                "object": obj,
                "is_edit": True,
                "active_page": "school",
                "page_title": self.page_title,
            },
        )

    def post(self, request, pk):
        obj = self.get_object(request, pk)
        form = StudentForm(request.POST, request.FILES, instance=obj, tenant=request.hrm_tenant)
        if form.is_valid():
            form.save()
            messages.success(request, "Student updated.")
            return redirect("school:student_list")
        return render(
            request,
            "school/student_form.html",
            {"form": form, "object": obj, "is_edit": True, "active_page": "school", "page_title": self.page_title},
        )


class StaffListView(SchoolAdminMixin, SchoolPageContextMixin, ListView):
    template_name = "school/staff_list.html"
    context_object_name = "rows"
    paginate_by = 30
    page_title = "Staff"
    permission_codename = "school.view_staff"

    def get_queryset(self):
        qs = Staff.objects.filter(tenant=self.request.hrm_tenant)
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(name__icontains=q)
        return qs.order_by("name")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["selected"] = {"q": self.request.GET.get("q", "")}
        return ctx


class StaffCreateView(SchoolAdminMixin, SchoolPageContextMixin, View):
    page_title = "Add staff"
    permission_codename = "school.manage"

    def get(self, request):
        return render(
            request,
            "school/staff_form.html",
            {
                "form": StaffForm(tenant=request.hrm_tenant),
                "is_edit": False,
                "active_page": "school",
                "page_title": self.page_title,
            },
        )

    def post(self, request):
        form = StaffForm(request.POST, request.FILES, tenant=request.hrm_tenant)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            messages.success(request, "Staff saved.")
            return redirect("school:staff_list")
        return render(
            request,
            "school/staff_form.html",
            {"form": form, "is_edit": False, "active_page": "school", "page_title": self.page_title},
        )


class StaffUpdateView(SchoolAdminMixin, SchoolPageContextMixin, View):
    page_title = "Edit staff"
    permission_codename = "school.manage"

    def get_object(self, request, pk):
        return get_object_or_404(Staff, tenant=request.hrm_tenant, pk=pk)

    def get(self, request, pk):
        obj = self.get_object(request, pk)
        return render(
            request,
            "school/staff_form.html",
            {
                "form": StaffForm(instance=obj, tenant=request.hrm_tenant),
                "object": obj,
                "is_edit": True,
                "active_page": "school",
                "page_title": self.page_title,
            },
        )

    def post(self, request, pk):
        obj = self.get_object(request, pk)
        form = StaffForm(request.POST, request.FILES, instance=obj, tenant=request.hrm_tenant)
        if form.is_valid():
            form.save()
            messages.success(request, "Staff updated.")
            return redirect("school:staff_list")
        return render(
            request,
            "school/staff_form.html",
            {"form": form, "object": obj, "is_edit": True, "active_page": "school", "page_title": self.page_title},
        )


class AcademicYearListView(SchoolAdminMixin, SchoolPageContextMixin, ListView):
    template_name = "school/academic_year_list.html"
    context_object_name = "rows"
    paginate_by = 30
    page_title = "Academic years"
    permission_codename = "school.view_academicyear"

    def get_queryset(self):
        return AcademicYear.objects.filter(tenant=self.request.hrm_tenant).order_by("-start_date", "-id")


class ClassListView(SchoolAdminMixin, SchoolPageContextMixin, ListView):
    template_name = "school/class_list.html"
    context_object_name = "rows"
    paginate_by = 30
    page_title = "Classes"
    permission_codename = "school.view_class"

    def get_queryset(self):
        return SchoolClass.objects.filter(tenant=self.request.hrm_tenant).select_related("academic_year", "class_teacher").order_by(
            "numeric_level", "name"
        )


class SectionListView(SchoolAdminMixin, SchoolPageContextMixin, ListView):
    template_name = "school/section_list.html"
    context_object_name = "rows"
    paginate_by = 30
    page_title = "Sections"
    permission_codename = "school.view_section"

    def get_queryset(self):
        return Section.objects.filter(tenant=self.request.hrm_tenant).select_related("class_level").order_by(
            "class_level__numeric_level", "name"
        )


class SubjectListView(SchoolAdminMixin, SchoolPageContextMixin, ListView):
    template_name = "school/subject_list.html"
    context_object_name = "rows"
    paginate_by = 50
    page_title = "Subjects"
    permission_codename = "school.view_subject"

    def get_queryset(self):
        return Subject.objects.filter(tenant=self.request.hrm_tenant).select_related("class_level").order_by(
            "class_level__numeric_level", "code"
        )


class StudentAttendanceListView(SchoolAdminMixin, SchoolPageContextMixin, ListView):
    template_name = "school/student_attendance_list.html"
    context_object_name = "rows"
    paginate_by = 50
    page_title = "Student attendance"
    permission_codename = "school.view_attendance"

    def get_queryset(self):
        return StudentAttendance.objects.filter(tenant=self.request.hrm_tenant).select_related("student").order_by("-date", "student__name")


class StaffAttendanceListView(SchoolAdminMixin, SchoolPageContextMixin, ListView):
    template_name = "school/staff_attendance_list.html"
    context_object_name = "rows"
    paginate_by = 50
    page_title = "Staff attendance"
    permission_codename = "school.view_attendance"

    def get_queryset(self):
        return StaffAttendance.objects.filter(tenant=self.request.hrm_tenant).select_related("staff").order_by("-date", "staff__name")


class ExamListView(SchoolAdminMixin, SchoolPageContextMixin, ListView):
    template_name = "school/exam_list.html"
    context_object_name = "rows"
    paginate_by = 30
    page_title = "Exams"
    permission_codename = "school.view_exam"

    def get_queryset(self):
        return Exam.objects.filter(tenant=self.request.hrm_tenant).select_related("academic_year", "class_level").order_by("-start_date", "-id")


class FeeCategoryListView(SchoolAdminMixin, SchoolPageContextMixin, ListView):
    template_name = "school/fee_category_list.html"
    context_object_name = "rows"
    paginate_by = 50
    page_title = "Fee categories"
    permission_codename = "school.view_fee"

    def get_queryset(self):
        return FeeCategory.objects.filter(tenant=self.request.hrm_tenant).order_by("name")


class FeeStructureListView(SchoolAdminMixin, SchoolPageContextMixin, ListView):
    template_name = "school/fee_structure_list.html"
    context_object_name = "rows"
    paginate_by = 50
    page_title = "Fee structures"
    permission_codename = "school.view_fee"

    def get_queryset(self):
        return FeeStructure.objects.filter(tenant=self.request.hrm_tenant).select_related(
            "academic_year", "class_level", "fee_category"
        ).order_by("-id")


class FeeDiscountListView(SchoolAdminMixin, SchoolPageContextMixin, ListView):
    template_name = "school/fee_discount_list.html"
    context_object_name = "rows"
    paginate_by = 50
    page_title = "Fee discounts"
    permission_codename = "school.view_fee"

    def get_queryset(self):
        return FeeDiscount.objects.filter(tenant=self.request.hrm_tenant).select_related("student", "fee_category").order_by("-id")


class FeeCollectionListView(SchoolAdminMixin, SchoolPageContextMixin, ListView):
    template_name = "school/fee_collection_list.html"
    context_object_name = "rows"
    paginate_by = 50
    page_title = "Fee collections"
    permission_codename = "school.view_fee"

    def get_queryset(self):
        return FeeCollection.objects.filter(tenant=self.request.hrm_tenant).select_related(
            "student", "fee_structure", "fee_structure__fee_category"
        ).order_by("-payment_date", "-id")


class SMSLogListView(SchoolAdminMixin, SchoolPageContextMixin, ListView):
    template_name = "school/sms_log_list.html"
    context_object_name = "rows"
    paginate_by = 50
    page_title = "SMS logs"
    permission_codename = "school.view_sms_log"

    def get_queryset(self):
        return SMSLog.objects.filter(tenant=self.request.hrm_tenant).select_related("related_student").order_by("-created_at")

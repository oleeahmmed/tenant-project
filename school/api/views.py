from django.db.models import Sum
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from auth_tenants.permissions import TenantAPIView, RequirePermission, get_tenant
from school.models import (
    AcademicYear,
    Exam,
    ExamResult,
    ExamSchedule,
    FeeCategory,
    FeeCollection,
    FeeDiscount,
    FeeStructure,
    SMSLog,
    SchoolClass,
    Section,
    Staff,
    StaffAttendance,
    Student,
    StudentAttendance,
    Subject,
    SubjectTeacher,
)

from .serializers import (
    AcademicYearSerializer,
    ExamResultSerializer,
    ExamScheduleSerializer,
    ExamSerializer,
    FeeCategorySerializer,
    FeeCollectionSerializer,
    FeeDiscountSerializer,
    FeeStructureSerializer,
    SMSLogSerializer,
    SchoolClassSerializer,
    SectionSerializer,
    StaffAttendanceSerializer,
    StaffSerializer,
    StudentAttendanceSerializer,
    StudentSerializer,
    SubjectSerializer,
    SubjectTeacherSerializer,
)


class TenantScopedModelViewSet(TenantAPIView, viewsets.ModelViewSet):
    """🎯 UNIFIED SCHOOL API BASE"""
    module_code = "school"
    tenant_field = "tenant"
    model_class = None

    def get_queryset(self):
        tenant = self.get_tenant()
        return self.model_class.objects.filter(**{self.tenant_field: tenant})

    def perform_create(self, serializer):
        tenant = self.get_tenant()
        data = {self.tenant_field: tenant}
        model_field_names = {f.name for f in serializer.Meta.model._meta.fields}
        if "created_by" in model_field_names:
            data["created_by"] = self.request.user
        serializer.save(**data)


class AcademicYearViewSet(TenantScopedModelViewSet):
    serializer_class = AcademicYearSerializer
    model_class = AcademicYear
    required_permission = "school.view_academicyear"


class SchoolClassViewSet(TenantScopedModelViewSet):
    serializer_class = SchoolClassSerializer
    model_class = SchoolClass
    required_permission = "school.view_class"


class SectionViewSet(TenantScopedModelViewSet):
    serializer_class = SectionSerializer
    model_class = Section
    required_permission = "school.view_section"


class SubjectViewSet(TenantScopedModelViewSet):
    serializer_class = SubjectSerializer
    model_class = Subject
    required_permission = "school.view_subject"


class StudentViewSet(TenantScopedModelViewSet):
    serializer_class = StudentSerializer
    model_class = Student
    required_permission = "school.view_student"

    @action(detail=True, methods=["post"])
    def promote(self, request, pk=None):
        student = self.get_object()
        next_class = request.data.get("next_class_id")
        next_section = request.data.get("next_section_id")
        if next_class:
            student.current_class_id = next_class
        if next_section:
            student.current_section_id = next_section
        student.roll_number = ""
        student.save()
        return self.success_response({"detail": "Student promoted"})


class StaffViewSet(TenantScopedModelViewSet):
    serializer_class = StaffSerializer
    model_class = Staff
    required_permission = "school.view_staff"


class SubjectTeacherViewSet(TenantScopedModelViewSet):
    serializer_class = SubjectTeacherSerializer
    model_class = SubjectTeacher
    required_permission = "school.view_subject"


class StudentAttendanceViewSet(TenantScopedModelViewSet):
    serializer_class = StudentAttendanceSerializer
    model_class = StudentAttendance
    required_permission = "school.view_attendance"


class StaffAttendanceViewSet(TenantScopedModelViewSet):
    serializer_class = StaffAttendanceSerializer
    model_class = StaffAttendance
    required_permission = "school.view_attendance"


class ExamViewSet(TenantScopedModelViewSet):
    serializer_class = ExamSerializer
    model_class = Exam
    required_permission = "school.view_exam"


class ExamScheduleViewSet(TenantScopedModelViewSet):
    serializer_class = ExamScheduleSerializer
    model_class = ExamSchedule
    tenant_field = "exam__tenant"
    required_permission = "school.view_exam"


class ExamResultViewSet(TenantScopedModelViewSet):
    serializer_class = ExamResultSerializer
    model_class = ExamResult
    required_permission = "school.enter_result"


class FeeCategoryViewSet(TenantScopedModelViewSet):
    serializer_class = FeeCategorySerializer
    model_class = FeeCategory
    required_permission = "school.view_fee"


class FeeStructureViewSet(TenantScopedModelViewSet):
    serializer_class = FeeStructureSerializer
    model_class = FeeStructure
    required_permission = "school.view_fee"


class FeeDiscountViewSet(TenantScopedModelViewSet):
    serializer_class = FeeDiscountSerializer
    model_class = FeeDiscount
    required_permission = "school.give_discount"


class FeeCollectionViewSet(TenantScopedModelViewSet):
    serializer_class = FeeCollectionSerializer
    model_class = FeeCollection
    required_permission = "school.collect_fee"


class SMSLogViewSet(TenantScopedModelViewSet):
    serializer_class = SMSLogSerializer
    model_class = SMSLog
    required_permission = "school.view_sms_log"


class DashboardReportAPIView(TenantAPIView):
    """🎯 SCHOOL DASHBOARD API"""
    module_code = "school"
    required_permission = "school.view_reports"

    def get(self, request):
        tenant = self.get_tenant()
        data = {
            "students": Student.objects.filter(tenant=tenant, status=Student.Status.ACTIVE).count(),
            "staff": Staff.objects.filter(tenant=tenant, status=Staff.Status.ACTIVE).count(),
            "fees_collected": float(
                FeeCollection.objects.filter(tenant=tenant, status=FeeCollection.Status.PAID).aggregate(v=Sum("amount_paid"))["v"] or 0
            ),
            "fees_due": float(
                FeeCollection.objects.filter(tenant=tenant).exclude(status=FeeCollection.Status.PAID).aggregate(v=Sum("amount_due"))["v"] or 0
            ),
        }
        return self.success_response(data)

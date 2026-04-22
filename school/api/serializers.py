from rest_framework import serializers

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


class BaseTenantSerializer(serializers.ModelSerializer):
    class Meta:
        fields = "__all__"


class AcademicYearSerializer(BaseTenantSerializer):
    class Meta(BaseTenantSerializer.Meta):
        model = AcademicYear


class StaffSerializer(BaseTenantSerializer):
    class Meta(BaseTenantSerializer.Meta):
        model = Staff


class SchoolClassSerializer(BaseTenantSerializer):
    class Meta(BaseTenantSerializer.Meta):
        model = SchoolClass


class SectionSerializer(BaseTenantSerializer):
    class Meta(BaseTenantSerializer.Meta):
        model = Section


class SubjectSerializer(BaseTenantSerializer):
    class Meta(BaseTenantSerializer.Meta):
        model = Subject


class StudentSerializer(BaseTenantSerializer):
    class Meta(BaseTenantSerializer.Meta):
        model = Student


class SubjectTeacherSerializer(BaseTenantSerializer):
    class Meta(BaseTenantSerializer.Meta):
        model = SubjectTeacher


class StudentAttendanceSerializer(BaseTenantSerializer):
    class Meta(BaseTenantSerializer.Meta):
        model = StudentAttendance


class StaffAttendanceSerializer(BaseTenantSerializer):
    class Meta(BaseTenantSerializer.Meta):
        model = StaffAttendance


class ExamSerializer(BaseTenantSerializer):
    class Meta(BaseTenantSerializer.Meta):
        model = Exam


class ExamScheduleSerializer(BaseTenantSerializer):
    class Meta(BaseTenantSerializer.Meta):
        model = ExamSchedule


class ExamResultSerializer(BaseTenantSerializer):
    class Meta(BaseTenantSerializer.Meta):
        model = ExamResult


class FeeCategorySerializer(BaseTenantSerializer):
    class Meta(BaseTenantSerializer.Meta):
        model = FeeCategory


class FeeStructureSerializer(BaseTenantSerializer):
    class Meta(BaseTenantSerializer.Meta):
        model = FeeStructure


class FeeDiscountSerializer(BaseTenantSerializer):
    class Meta(BaseTenantSerializer.Meta):
        model = FeeDiscount


class FeeCollectionSerializer(BaseTenantSerializer):
    class Meta(BaseTenantSerializer.Meta):
        model = FeeCollection


class SMSLogSerializer(BaseTenantSerializer):
    class Meta(BaseTenantSerializer.Meta):
        model = SMSLog

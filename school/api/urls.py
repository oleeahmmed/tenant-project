from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AcademicYearViewSet,
    DashboardReportAPIView,
    ExamResultViewSet,
    ExamScheduleViewSet,
    ExamViewSet,
    FeeCategoryViewSet,
    FeeCollectionViewSet,
    FeeDiscountViewSet,
    FeeStructureViewSet,
    SMSLogViewSet,
    SchoolClassViewSet,
    SectionViewSet,
    StaffAttendanceViewSet,
    StaffViewSet,
    StudentAttendanceViewSet,
    StudentViewSet,
    SubjectTeacherViewSet,
    SubjectViewSet,
)

router = DefaultRouter()
router.register(r"academic-years", AcademicYearViewSet, basename="academic-year")
router.register(r"classes", SchoolClassViewSet, basename="class")
router.register(r"sections", SectionViewSet, basename="section")
router.register(r"subjects", SubjectViewSet, basename="subject")
router.register(r"students", StudentViewSet, basename="student")
router.register(r"staff", StaffViewSet, basename="staff")
router.register(r"subject-teachers", SubjectTeacherViewSet, basename="subject-teacher")
router.register(r"attendance/students", StudentAttendanceViewSet, basename="student-attendance")
router.register(r"attendance/staff", StaffAttendanceViewSet, basename="staff-attendance")
router.register(r"exams", ExamViewSet, basename="exam")
router.register(r"exam-schedules", ExamScheduleViewSet, basename="exam-schedule")
router.register(r"exam-results", ExamResultViewSet, basename="exam-result")
router.register(r"fee/categories", FeeCategoryViewSet, basename="fee-category")
router.register(r"fee/structures", FeeStructureViewSet, basename="fee-structure")
router.register(r"fee/discounts", FeeDiscountViewSet, basename="fee-discount")
router.register(r"fee/collections", FeeCollectionViewSet, basename="fee-collection")
router.register(r"sms/logs", SMSLogViewSet, basename="sms-log")

urlpatterns = [
    path("reports/dashboard/", DashboardReportAPIView.as_view(), name="reports-dashboard"),
    path("", include(router.urls)),
]

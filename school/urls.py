from django.urls import path

from . import views

app_name = "school"

urlpatterns = [
    path("", views.SchoolDashboardView.as_view(), name="dashboard"),
    path("guide/", views.SchoolGuideView.as_view(), name="guide"),
    path("academic/years/", views.AcademicYearListView.as_view(), name="academic_year_list"),
    path("academic/classes/", views.ClassListView.as_view(), name="class_list"),
    path("academic/sections/", views.SectionListView.as_view(), name="section_list"),
    path("academic/subjects/", views.SubjectListView.as_view(), name="subject_list"),
    path("students/add/", views.StudentCreateView.as_view(), name="student_create"),
    path("students/<int:pk>/edit/", views.StudentUpdateView.as_view(), name="student_update"),
    path("students/", views.StudentListView.as_view(), name="student_list"),
    path("staff/add/", views.StaffCreateView.as_view(), name="staff_create"),
    path("staff/<int:pk>/edit/", views.StaffUpdateView.as_view(), name="staff_update"),
    path("staff/", views.StaffListView.as_view(), name="staff_list"),
    path("attendance/students/", views.StudentAttendanceListView.as_view(), name="student_attendance_list"),
    path("attendance/staff/", views.StaffAttendanceListView.as_view(), name="staff_attendance_list"),
    path("exams/", views.ExamListView.as_view(), name="exam_list"),
    path("fees/categories/", views.FeeCategoryListView.as_view(), name="fee_category_list"),
    path("fees/structures/", views.FeeStructureListView.as_view(), name="fee_structure_list"),
    path("fees/discounts/", views.FeeDiscountListView.as_view(), name="fee_discount_list"),
    path("fees/collections/", views.FeeCollectionListView.as_view(), name="fee_collection_list"),
    path("sms/logs/", views.SMSLogListView.as_view(), name="sms_log_list"),
]

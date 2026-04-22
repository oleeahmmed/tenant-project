from django.contrib import admin

from . import models


ALL_MODELS = [
    models.AcademicYear,
    models.SchoolClass,
    models.Section,
    models.Subject,
    models.Student,
    models.Staff,
    models.SubjectTeacher,
    models.StudentAttendance,
    models.StaffAttendance,
    models.Exam,
    models.ExamSchedule,
    models.ExamResult,
    models.FeeCategory,
    models.FeeStructure,
    models.FeeDiscount,
    models.FeeCollection,
    models.SMSLog,
]

for m in ALL_MODELS:
    admin.site.register(m)

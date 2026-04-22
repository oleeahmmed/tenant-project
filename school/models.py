from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AcademicYear(TimeStampedModel):
    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="school_academic_years")
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        unique_together = [("tenant", "name")]
        ordering = ["-start_date"]

    def __str__(self):
        return self.name


class Staff(TimeStampedModel):
    class Designation(models.TextChoices):
        PRINCIPAL = "PRINCIPAL", "Principal"
        TEACHER = "TEACHER", "Teacher"
        ASSISTANT_TEACHER = "ASSISTANT_TEACHER", "Assistant Teacher"
        ACCOUNTANT = "ACCOUNTANT", "Accountant"
        PEON = "PEON", "Peon"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        RESIGNED = "RESIGNED", "Resigned"

    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="school_staffs")
    employee_id = models.CharField(max_length=30)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="school_staff_profile")
    name = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    nid_number = models.CharField(max_length=50, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    blood_group = models.CharField(max_length=10, blank=True)
    designation = models.CharField(max_length=30, choices=Designation.choices, default=Designation.TEACHER)
    department = models.CharField(max_length=120, blank=True)
    joining_date = models.DateField(default=timezone.now)
    qualification = models.TextField(blank=True)
    experience_years = models.PositiveSmallIntegerField(default=0)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    permanent_address = models.TextField(blank=True)
    present_address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_number = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(upload_to="school/staff/profile/", null=True, blank=True)
    nid_photo_front = models.ImageField(upload_to="school/staff/nid/", null=True, blank=True)
    nid_photo_back = models.ImageField(upload_to="school/staff/nid/", null=True, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="school_created_staffs")

    class Meta:
        unique_together = [("tenant", "employee_id")]
        ordering = ["name"]

    def __str__(self):
        return f"{self.employee_id} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.employee_id:
            prefix = timezone.now().strftime("EMP%y")
            last = Staff.objects.filter(tenant=self.tenant, employee_id__startswith=prefix).order_by("-id").first()
            seq = int(last.employee_id[-4:]) + 1 if last and last.employee_id[-4:].isdigit() else 1
            self.employee_id = f"{prefix}{seq:04d}"
        super().save(*args, **kwargs)


class SchoolClass(TimeStampedModel):
    class Shift(models.TextChoices):
        MORNING = "MORNING", "Morning"
        DAY = "DAY", "Day"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="school_classes")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="classes")
    name = models.CharField(max_length=120)
    numeric_level = models.PositiveSmallIntegerField()
    class_teacher = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_classes")
    shift = models.CharField(max_length=10, choices=Shift.choices, default=Shift.DAY)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        unique_together = [("tenant", "academic_year", "name", "shift")]
        ordering = ["numeric_level", "name"]

    def __str__(self):
        return self.name


class Section(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="school_sections")
    class_level = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="sections")
    name = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField(default=50)
    room_number = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        unique_together = [("tenant", "class_level", "name")]
        ordering = ["class_level__numeric_level", "name"]

    def __str__(self):
        return f"{self.class_level.name} - {self.name}"


class Subject(TimeStampedModel):
    class SubjectType(models.TextChoices):
        COMPULSORY = "COMPULSORY", "Compulsory"
        OPTIONAL = "OPTIONAL", "Optional"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="school_subjects")
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=20)
    class_level = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="subjects")
    subject_type = models.CharField(max_length=20, choices=SubjectType.choices, default=SubjectType.COMPULSORY)
    full_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    pass_marks = models.DecimalField(max_digits=6, decimal_places=2, default=33)

    class Meta:
        unique_together = [("tenant", "class_level", "code")]
        ordering = ["class_level__numeric_level", "code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Student(TimeStampedModel):
    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        TRANSFERRED = "TRANSFERRED", "Transferred"
        PASSED_OUT = "PASSED_OUT", "Passed out"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="school_students")
    registration_number = models.CharField(max_length=30, unique=True)
    roll_number = models.CharField(max_length=30, blank=True)
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=Gender.choices)
    blood_group = models.CharField(max_length=10, blank=True)
    religion = models.CharField(max_length=50, blank=True)
    nationality = models.CharField(max_length=50, default="Bangladeshi")
    current_class = models.ForeignKey(SchoolClass, on_delete=models.SET_NULL, null=True, related_name="students")
    current_section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, related_name="students")
    admission_date = models.DateField(default=timezone.now)
    father_name = models.CharField(max_length=255, blank=True)
    father_mobile = models.CharField(max_length=20, blank=True)
    father_occupation = models.CharField(max_length=120, blank=True)
    mother_name = models.CharField(max_length=255, blank=True)
    mother_mobile = models.CharField(max_length=20, blank=True)
    guardian_name = models.CharField(max_length=255, blank=True)
    guardian_mobile = models.CharField(max_length=20, blank=True)
    guardian_relation = models.CharField(max_length=50, blank=True)
    permanent_address = models.TextField(blank=True)
    present_address = models.TextField(blank=True)
    previous_school = models.CharField(max_length=255, blank=True)
    transfer_certificate_number = models.CharField(max_length=100, blank=True)
    profile_photo = models.ImageField(upload_to="school/students/profile/", null=True, blank=True)
    birth_certificate_photo = models.ImageField(upload_to="school/students/certificates/", null=True, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="school_created_students")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.registration_number} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.registration_number:
            prefix = timezone.now().strftime("STD%y")
            last = Student.objects.filter(registration_number__startswith=prefix).order_by("-id").first()
            seq = int(last.registration_number[-5:]) + 1 if last and last.registration_number[-5:].isdigit() else 1
            self.registration_number = f"{prefix}{seq:05d}"
        if self.current_class_id and self.current_section_id and not self.roll_number:
            count = Student.objects.filter(
                tenant=self.tenant,
                current_class=self.current_class,
                current_section=self.current_section,
            ).exclude(pk=self.pk).count() + 1
            self.roll_number = f"{self.current_class.numeric_level:02d}{self.current_section.name}{count:03d}"
        super().save(*args, **kwargs)


class SubjectTeacher(models.Model):
    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="school_subject_teachers")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="teacher_assignments")
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="subject_assignments")
    teacher = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="subject_assignments")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="subject_teacher_assignments")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("tenant", "subject", "section", "academic_year")]

    def __str__(self):
        return f"{self.subject} - {self.section} - {self.teacher}"


class StudentAttendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        LATE = "LATE", "Late"
        HOLIDAY = "HOLIDAY", "Holiday"
        LEAVE = "LEAVE", "Leave"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="school_student_attendance")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance_rows")
    date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    note = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="marked_student_attendance")
    sms_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("tenant", "student", "date")]
        ordering = ["-date", "student__name"]


class StaffAttendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        LATE = "LATE", "Late"
        LEAVE = "LEAVE", "Leave"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="school_staff_attendance")
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="attendance_rows")
    date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    note = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="marked_staff_attendance")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("tenant", "staff", "date")]
        ordering = ["-date", "staff__name"]


class Exam(TimeStampedModel):
    class ExamType(models.TextChoices):
        HALF_YEARLY = "HALF_YEARLY", "Half yearly"
        ANNUAL = "ANNUAL", "Annual"
        CLASS_TEST = "CLASS_TEST", "Class test"
        MONTHLY_TEST = "MONTHLY_TEST", "Monthly test"

    class Status(models.TextChoices):
        UPCOMING = "UPCOMING", "Upcoming"
        ONGOING = "ONGOING", "Ongoing"
        COMPLETED = "COMPLETED", "Completed"
        RESULT_PUBLISHED = "RESULT_PUBLISHED", "Result published"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="school_exams")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="exams")
    name = models.CharField(max_length=255)
    exam_type = models.CharField(max_length=20, choices=ExamType.choices)
    class_level = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="exams")
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPCOMING)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="school_created_exams")

    class Meta:
        ordering = ["-start_date"]


class ExamSchedule(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="schedules")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="exam_schedules")
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    full_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    pass_marks = models.DecimalField(max_digits=6, decimal_places=2, default=33)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("exam", "subject")]


class ExamResult(TimeStampedModel):
    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="school_exam_results")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="results")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="exam_results")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="results")
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    grade = models.CharField(max_length=5, blank=True)
    grade_point = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    remarks = models.CharField(max_length=255, blank=True)
    entered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="entered_exam_results")

    class Meta:
        unique_together = [("tenant", "exam", "student", "subject")]
        ordering = ["student__name"]

    def save(self, *args, **kwargs):
        total = float(self.subject.full_marks or 100)
        pct = float(self.marks_obtained or 0) / total * 100 if total else 0
        if pct >= 80:
            self.grade, self.grade_point = "A+", 5.00
        elif pct >= 70:
            self.grade, self.grade_point = "A", 4.00
        elif pct >= 60:
            self.grade, self.grade_point = "A-", 3.50
        elif pct >= 50:
            self.grade, self.grade_point = "B", 3.00
        elif pct >= 40:
            self.grade, self.grade_point = "C", 2.00
        elif pct >= 33:
            self.grade, self.grade_point = "D", 1.00
        else:
            self.grade, self.grade_point = "F", 0.00
        super().save(*args, **kwargs)


class FeeCategory(models.Model):
    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="school_fee_categories")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_monthly = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("tenant", "name")]


class FeeStructure(TimeStampedModel):
    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="school_fee_structures")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="fee_structures")
    class_level = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="fee_structures")
    fee_category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE, related_name="structures")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date_day = models.PositiveSmallIntegerField(default=10)
    late_fine_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        unique_together = [("tenant", "academic_year", "class_level", "fee_category")]


class FeeDiscount(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = "PERCENTAGE", "Percentage"
        FIXED_AMOUNT = "FIXED_AMOUNT", "Fixed amount"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="school_fee_discounts")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="fee_discounts")
    fee_category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE, related_name="discounts")
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=120)
    valid_from = models.DateField()
    valid_to = models.DateField()
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="approved_fee_discounts")
    created_at = models.DateTimeField(auto_now_add=True)


class FeeCollection(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "CASH", "Cash"
        BANK_TRANSFER = "BANK_TRANSFER", "Bank transfer"
        CHEQUE = "CHEQUE", "Cheque"
        MOBILE_BANKING = "MOBILE_BANKING", "Mobile banking"

    class Status(models.TextChoices):
        PAID = "PAID", "Paid"
        PARTIAL = "PARTIAL", "Partial"
        UNPAID = "UNPAID", "Unpaid"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="school_fee_collections")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="fee_collections")
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name="collections")
    payment_month = models.DateField()
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    transaction_reference = models.CharField(max_length=255, blank=True)
    receipt_number = models.CharField(max_length=50, unique=True, blank=True)
    late_fine = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UNPAID)
    collected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="collected_school_fees")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date", "-id"]

    def clean(self):
        if self.amount_paid > (self.amount_due - self.discount_amount + self.late_fine):
            raise ValidationError("Amount paid cannot exceed payable amount.")

    def save(self, *args, **kwargs):
        payable = (self.amount_due - self.discount_amount) + self.late_fine
        if self.amount_paid <= 0:
            self.status = self.Status.UNPAID
        elif self.amount_paid < payable:
            self.status = self.Status.PARTIAL
        else:
            self.status = self.Status.PAID
        if not self.receipt_number:
            self.receipt_number = f"SRC{timezone.now().strftime('%Y%m%d%H%M%S%f')}"
        super().save(*args, **kwargs)


class SMSLog(models.Model):
    class MessageType(models.TextChoices):
        ATTENDANCE = "ATTENDANCE", "Attendance"
        FEE_REMINDER = "FEE_REMINDER", "Fee reminder"
        EXAM_NOTICE = "EXAM_NOTICE", "Exam notice"
        RESULT = "RESULT", "Result"
        GENERAL = "GENERAL", "General"

    class Status(models.TextChoices):
        SENT = "SENT", "Sent"
        FAILED = "FAILED", "Failed"
        PENDING = "PENDING", "Pending"

    tenant = models.ForeignKey("auth_tenants.Tenant", on_delete=models.CASCADE, related_name="school_sms_logs")
    recipient_mobile = models.CharField(max_length=20)
    recipient_name = models.CharField(max_length=255, blank=True)
    message_text = models.TextField()
    message_type = models.CharField(max_length=20, choices=MessageType.choices)
    related_student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name="sms_logs")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="sent_school_sms")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

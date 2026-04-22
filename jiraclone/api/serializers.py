from rest_framework import serializers

from foundation.models import Customer
from jiraclone.models import Issue, JiraProject, ProjectDepartmentAssignment


class BoardIssueSerializer(serializers.ModelSerializer):
    issue_key = serializers.CharField(read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    status = serializers.SerializerMethodField()
    issue_type = serializers.SerializerMethodField()
    assignees = serializers.SerializerMethodField()

    class Meta:
        model = Issue
        fields = [
            "id",
            "issue_key",
            "summary",
            "description",
            "priority",
            "priority_display",
            "due_date",
            "status",
            "issue_type",
            "assignees",
            "parent_id",
            "updated_at",
        ]

    def get_status(self, obj):
        return {"id": obj.status_id, "name": obj.status.name}

    def get_issue_type(self, obj):
        return {"id": obj.issue_type_id, "name": obj.issue_type.name}

    def get_assignees(self, obj):
        return [{"id": u.id, "name": u.name} for u in obj.assignees.all()]


class ProjectDepartmentAssignmentSerializer(serializers.ModelSerializer):
    department = serializers.SerializerMethodField()
    employees = serializers.SerializerMethodField()

    class Meta:
        model = ProjectDepartmentAssignment
        fields = ["id", "order", "department", "employees"]

    def get_department(self, obj):
        d = obj.department
        return {"id": d.id, "name": d.name, "code": d.code}

    def get_employees(self, obj):
        return [
            {"id": u.id, "name": u.name, "employee_code": u.email or "", "user_id": u.id}
            for u in obj.users.all().order_by("name")
        ]


class JiraProjectSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = JiraProject
        fields = [
            "id",
            "key",
            "name",
            "description",
            "customer_id",
            "customer_name",
            "is_active",
            "created_at",
            "updated_at",
        ]


class JiraIssueCreateSerializer(serializers.ModelSerializer):
    assignee_ids = serializers.ListField(child=serializers.IntegerField(), required=False, allow_empty=True, write_only=True)

    class Meta:
        model = Issue
        fields = [
            "summary",
            "description",
            "priority",
            "status",
            "issue_type",
            "due_date",
            "parent",
            "assignee_ids",
        ]


class JiraOnboardingCustomerSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source="customer_code", read_only=True)

    class Meta:
        model = Customer
        fields = ["id", "name", "code", "email", "phone", "city", "country"]

from rest_framework import serializers

from jiraclone.models import Issue, ProjectDepartmentAssignment


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

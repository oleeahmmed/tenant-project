from django.utils import timezone
from rest_framework import serializers

from auth_tenants.models import User
from screenhot.models import AttendanceRecord, ScreenshotRecord, VideoJob


class ScreenshotUploadSerializer(serializers.ModelSerializer):
    captured_at = serializers.DateTimeField(required=False)
    user_id = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = ScreenshotRecord
        fields = [
            "id",
            "image",
            "captured_at",
            "relative_path",
            "activity_status",
            "metadata",
            "user_id",
        ]
        read_only_fields = ["id"]

    def validate_captured_at(self, value):
        if value > timezone.now() + timezone.timedelta(minutes=5):
            raise serializers.ValidationError("Captured time cannot be far in the future.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        tenant = self.context["tenant"]
        target_user = request.user
        requested_user_id = attrs.pop("user_id", None)
        if requested_user_id:
            if request.user.role not in ("tenant_admin", "super_admin"):
                raise serializers.ValidationError("Only admins can upload for another employee.")
            target_user = User.objects.filter(pk=requested_user_id, tenant=tenant, is_active=True).first()
            if not target_user:
                raise serializers.ValidationError("Invalid employee for tenant.")
        attrs["tenant"] = tenant
        attrs["user"] = target_user
        return attrs


class ScreenshotListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    employee = serializers.SerializerMethodField()

    class Meta:
        model = ScreenshotRecord
        fields = [
            "id",
            "captured_at",
            "relative_path",
            "activity_status",
            "metadata",
            "image_url",
            "employee",
        ]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if not obj.image:
            return None
        if request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url

    def get_employee(self, obj):
        return {
            "id": obj.user_id,
            "name": getattr(obj.user, "name", "") or getattr(obj.user, "email", f"User {obj.user_id}"),
            "email": getattr(obj.user, "email", ""),
        }


class AttendanceSerializer(serializers.ModelSerializer):
    duration_seconds = serializers.IntegerField(read_only=True)
    employee = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceRecord
        fields = [
            "id",
            "check_in",
            "check_out",
            "activity_status",
            "last_activity",
            "duration_seconds",
            "employee",
        ]

    def get_employee(self, obj):
        return {
            "id": obj.user_id,
            "name": getattr(obj.user, "name", "") or getattr(obj.user, "email", f"User {obj.user_id}"),
            "email": getattr(obj.user, "email", ""),
        }


class AttendanceActivitySerializer(serializers.Serializer):
    activity_status = serializers.ChoiceField(choices=AttendanceRecord.ActivityStatus.choices)


class VideoJobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoJob
        fields = [
            "target_user",
            "date_from",
            "date_to",
            "time_from",
            "time_to",
            "fps",
        ]

    def validate(self, attrs):
        if attrs["date_from"] > attrs["date_to"]:
            raise serializers.ValidationError("date_from must be less than or equal to date_to.")
        if attrs.get("fps", 0) <= 0:
            raise serializers.ValidationError("fps must be positive.")
        return attrs


class VideoJobSerializer(serializers.ModelSerializer):
    output_url = serializers.SerializerMethodField()
    target_employee = serializers.SerializerMethodField()
    requested_by_employee = serializers.SerializerMethodField()

    class Meta:
        model = VideoJob
        fields = [
            "id",
            "target_user",
            "date_from",
            "date_to",
            "time_from",
            "time_to",
            "fps",
            "status",
            "error_message",
            "output_url",
            "target_employee",
            "requested_by_employee",
            "created_at",
            "started_at",
            "completed_at",
        ]

    def get_output_url(self, obj):
        request = self.context.get("request")
        if not obj.output_file:
            return None
        if request:
            return request.build_absolute_uri(obj.output_file.url)
        return obj.output_file.url

    def get_target_employee(self, obj):
        return {
            "id": obj.target_user_id,
            "name": getattr(obj.target_user, "name", "") or getattr(obj.target_user, "email", f"User {obj.target_user_id}"),
        }

    def get_requested_by_employee(self, obj):
        return {
            "id": obj.requested_by_id,
            "name": getattr(obj.requested_by, "name", "") or getattr(obj.requested_by, "email", f"User {obj.requested_by_id}"),
        }

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_tenants.models import User
from hrm.tenant_scope import get_hrm_tenant, user_belongs_to_workspace_tenant
from jiraclone.models import JiraProject
from screenhot.models import AttendanceRecord, ScreenshotRecord, VideoJob
from screenhot.tasks import enqueue_video_job

from .serializers import (
    AttendanceActivitySerializer,
    AttendanceSerializer,
    ScreenshotListSerializer,
    ScreenshotUploadSerializer,
    VideoJobCreateSerializer,
    VideoJobSerializer,
)


class ScreenhotTenantScopedAPIView(APIView):
    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]
    required_permission = "screenhot.view"

    def get_tenant(self):
        if hasattr(self, "_screenhot_tenant"):
            return self._screenhot_tenant

        tenant = get_hrm_tenant(self.request)
        user = self.request.user
        if tenant is None or not user_belongs_to_workspace_tenant(user, tenant):
            self.permission_denied(self.request, message="No workspace tenant scope.")
        if not tenant.is_module_enabled("screenhot"):
            self.permission_denied(self.request, message="Screenhot module is disabled.")
        perm = getattr(self, "required_permission", "screenhot.view")
        if user.role != "super_admin" and not user.has_tenant_permission(perm):
            self.permission_denied(self.request, message="Missing permission.")

        self._screenhot_tenant = tenant
        return tenant

    def resolve_target_user(self, tenant, user_id):
        if not user_id:
            return self.request.user
        if self.request.user.role not in ("tenant_admin", "super_admin"):
            self.permission_denied(self.request, message="Only admins can operate for another employee.")
        target = User.objects.filter(pk=user_id, tenant=tenant, is_active=True).first()
        if not target:
            self.permission_denied(self.request, message="Invalid employee for tenant.")
        return target

    def resolve_project(self, tenant, project_key):
        key = (project_key or "").strip().upper()
        if not key:
            return None
        project = JiraProject.objects.filter(tenant=tenant, key=key, is_active=True).first()
        if not project:
            self.permission_denied(self.request, message="Invalid project for tenant.")
        return project

    def project_user_ids(self, project, department_id=None):
        rows = project.department_assignments.prefetch_related("users")
        if department_id:
            rows = rows.filter(department_id=department_id)
        user_ids = set()
        for row in rows:
            user_ids.update(row.users.values_list("id", flat=True))
        return user_ids


class ScreenshotUploadView(ScreenhotTenantScopedAPIView):
    required_permission = "screenhot.manage"

    def post(self, request):
        tenant = self.get_tenant()
        serializer = ScreenshotUploadSerializer(
            data=request.data,
            context={"request": request, "tenant": tenant},
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        output = ScreenshotListSerializer(instance, context={"request": request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class ScreenshotListView(ScreenhotTenantScopedAPIView):
    required_permission = "screenhot.view"

    def get(self, request):
        tenant = self.get_tenant()
        qs = ScreenshotRecord.objects.filter(tenant=tenant).select_related("user").order_by("-captured_at", "-id")
        employee_id = request.GET.get("employee_id")
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")
        if employee_id:
            qs = qs.filter(user_id=employee_id)
        if date_from:
            qs = qs.filter(captured_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(captured_at__date__lte=date_to)
        limit = min(max(int(request.GET.get("limit", 100)), 1), 500)
        data = ScreenshotListSerializer(qs[:limit], many=True, context={"request": request}).data
        return Response(data)


class ScreenshotDeleteView(ScreenhotTenantScopedAPIView):
    required_permission = "screenhot.delete"

    def delete(self, request, screenshot_id: int):
        tenant = self.get_tenant()
        shot = get_object_or_404(ScreenshotRecord, pk=screenshot_id, tenant=tenant)
        if request.user.role != "super_admin" and shot.user_id != request.user.id:
            self.permission_denied(request, message="Cannot delete another user's screenshot.")
        shot.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AttendanceCheckInView(ScreenhotTenantScopedAPIView):
    required_permission = "screenhot.manage"

    def post(self, request):
        tenant = self.get_tenant()
        target_user = self.resolve_target_user(tenant, request.data.get("user_id"))
        existing = AttendanceRecord.objects.filter(tenant=tenant, user=target_user, check_out__isnull=True).first()
        if existing:
            return Response({"detail": "Already checked in."}, status=status.HTTP_400_BAD_REQUEST)
        attendance = AttendanceRecord.objects.create(
            tenant=tenant,
            user=target_user,
            check_in=timezone.now(),
            last_activity=timezone.now(),
            activity_status=AttendanceRecord.ActivityStatus.ACTIVE,
        )
        return Response(AttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED)


class AttendanceCheckOutView(ScreenhotTenantScopedAPIView):
    required_permission = "screenhot.manage"

    def post(self, request):
        tenant = self.get_tenant()
        target_user = self.resolve_target_user(tenant, request.data.get("user_id"))
        attendance = AttendanceRecord.objects.filter(
            tenant=tenant, user=target_user, check_out__isnull=True
        ).order_by("-check_in", "-id").first()
        if not attendance:
            return Response({"detail": "No active check-in found."}, status=status.HTTP_400_BAD_REQUEST)
        attendance.check_out = timezone.now()
        attendance.last_activity = attendance.check_out
        attendance.save(update_fields=["check_out", "last_activity", "updated_at"])
        return Response(AttendanceSerializer(attendance).data)


class AttendanceActivityView(ScreenhotTenantScopedAPIView):
    required_permission = "screenhot.manage"

    def post(self, request):
        tenant = self.get_tenant()
        target_user = self.resolve_target_user(tenant, request.data.get("user_id"))
        active = AttendanceRecord.objects.filter(
            tenant=tenant, user=target_user, check_out__isnull=True
        ).order_by("-check_in", "-id").first()
        if not active:
            return Response({"detail": "No active check-in found."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = AttendanceActivitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        active.activity_status = serializer.validated_data["activity_status"]
        active.last_activity = timezone.now()
        active.save(update_fields=["activity_status", "last_activity", "updated_at"])
        return Response(AttendanceSerializer(active).data)


class AttendanceCurrentView(ScreenhotTenantScopedAPIView):
    required_permission = "screenhot.view"

    def get(self, request):
        tenant = self.get_tenant()
        active = AttendanceRecord.objects.filter(
            tenant=tenant, user=request.user, check_out__isnull=True
        ).order_by("-check_in", "-id").first()
        if not active:
            return Response({"active": False, "attendance": None})
        return Response({"active": True, "attendance": AttendanceSerializer(active).data})


class AttendanceListView(ScreenhotTenantScopedAPIView):
    required_permission = "screenhot.view"

    def get(self, request):
        tenant = self.get_tenant()
        qs = AttendanceRecord.objects.filter(tenant=tenant).select_related("user").order_by("-check_in", "-id")
        employee_id = request.GET.get("employee_id")
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")
        if employee_id:
            qs = qs.filter(user_id=employee_id)
        if date_from:
            qs = qs.filter(check_in__date__gte=date_from)
        if date_to:
            qs = qs.filter(check_in__date__lte=date_to)
        limit = min(max(int(request.GET.get("limit", 100)), 1), 500)
        return Response(AttendanceSerializer(qs[:limit], many=True).data)


class AttendanceDeleteView(ScreenhotTenantScopedAPIView):
    required_permission = "screenhot.delete"

    def delete(self, request, attendance_id: int):
        tenant = self.get_tenant()
        record = get_object_or_404(AttendanceRecord, pk=attendance_id, tenant=tenant)
        if request.user.role != "super_admin" and record.user_id != request.user.id:
            self.permission_denied(request, message="Cannot delete another user's attendance.")
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class VideoGenerateView(ScreenhotTenantScopedAPIView):
    required_permission = "screenhot.manage"

    def post(self, request):
        tenant = self.get_tenant()
        serializer = VideoJobCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = self.resolve_project(tenant, request.data.get("project_key"))
        department_id = request.data.get("department_id")

        target_user = serializer.validated_data["target_user"]
        if target_user.role != "super_admin" and target_user.tenant_id != tenant.id:
            return Response({"detail": "Target user is outside current tenant."}, status=status.HTTP_400_BAD_REQUEST)
        if target_user.role != "super_admin" and not User.objects.filter(pk=target_user.pk, tenant=tenant).exists():
            return Response({"detail": "Target user is invalid for tenant."}, status=status.HTTP_400_BAD_REQUEST)
        if project is not None:
            scoped_user_ids = self.project_user_ids(project, department_id=department_id)
            if target_user.id not in scoped_user_ids:
                return Response(
                    {"detail": "Target user is not assigned to the selected project/department."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        job = VideoJob.objects.create(
            tenant=tenant,
            requested_by=request.user,
            target_user=target_user,
            date_from=serializer.validated_data["date_from"],
            date_to=serializer.validated_data["date_to"],
            time_from=serializer.validated_data.get("time_from"),
            time_to=serializer.validated_data.get("time_to"),
            fps=serializer.validated_data.get("fps", 2),
            status=VideoJob.Status.PENDING,
        )
        enqueue_video_job(job.id)
        return Response(
            {"job_id": job.id, "status": job.status},
            status=status.HTTP_201_CREATED,
        )


class VideoStatusView(ScreenhotTenantScopedAPIView):
    required_permission = "screenhot.view"

    def get(self, request, job_id: int):
        tenant = self.get_tenant()
        job = get_object_or_404(VideoJob, pk=job_id, tenant=tenant)
        return Response(VideoJobSerializer(job, context={"request": request}).data)


class VideoJobListView(ScreenhotTenantScopedAPIView):
    required_permission = "screenhot.view"

    def get(self, request):
        tenant = self.get_tenant()
        qs = VideoJob.objects.filter(tenant=tenant).select_related("target_user", "requested_by").order_by("-created_at", "-id")
        employee_id = request.GET.get("employee_id")
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")
        if employee_id:
            qs = qs.filter(target_user_id=employee_id)
        if date_from:
            qs = qs.filter(date_from__gte=date_from)
        if date_to:
            qs = qs.filter(date_to__lte=date_to)
        limit = min(max(int(request.GET.get("limit", 100)), 1), 500)
        return Response(VideoJobSerializer(qs[:limit], many=True, context={"request": request}).data)


class VideoJobDeleteView(ScreenhotTenantScopedAPIView):
    required_permission = "screenhot.delete"

    def delete(self, request, job_id: int):
        tenant = self.get_tenant()
        job = get_object_or_404(VideoJob, pk=job_id, tenant=tenant)
        if job.output_file:
            job.output_file.delete(save=False)
        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployeeOptionsView(ScreenhotTenantScopedAPIView):
    required_permission = "screenhot.view"

    def get(self, request):
        tenant = self.get_tenant()
        project = self.resolve_project(tenant, request.GET.get("project_key"))
        department_id = request.GET.get("department_id")
        users = User.objects.filter(tenant=tenant, is_active=True)
        if project is not None:
            user_ids = self.project_user_ids(project, department_id=department_id)
            users = users.filter(id__in=user_ids)
        users = users.order_by("name", "email")
        data = [
            {
                "id": u.id,
                "name": (u.name or "").strip() or u.email,
                "email": u.email,
            }
            for u in users
        ]
        return Response(data)


class ProjectOptionsView(ScreenhotTenantScopedAPIView):
    required_permission = "screenhot.view"

    def get(self, request):
        tenant = self.get_tenant()
        projects = JiraProject.objects.filter(tenant=tenant, is_active=True).order_by("key")
        data = [
            {
                "id": p.id,
                "key": p.key,
                "name": p.name,
            }
            for p in projects
        ]
        return Response(data)


class DepartmentOptionsView(ScreenhotTenantScopedAPIView):
    required_permission = "screenhot.view"

    def get(self, request):
        tenant = self.get_tenant()
        project = self.resolve_project(tenant, request.GET.get("project_key"))
        if project is None:
            return Response([])
        rows = project.department_assignments.select_related("department").order_by("order", "department__name")
        data = [
            {
                "id": row.department_id,
                "name": row.department.name,
            }
            for row in rows
        ]
        return Response(data)


class LiveMonitorView(ScreenhotTenantScopedAPIView):
    required_permission = "screenhot.view"

    def get(self, request):
        tenant = self.get_tenant()
        now = timezone.now()
        live_cutoff = now - timezone.timedelta(seconds=30)
        employee_id = request.GET.get("employee_id")
        project = self.resolve_project(tenant, request.GET.get("project_key"))
        department_id = request.GET.get("department_id")
        users = User.objects.filter(tenant=tenant, is_active=True).order_by("name", "email")
        if project is not None:
            users = users.filter(id__in=self.project_user_ids(project, department_id=department_id))
        if employee_id:
            users = users.filter(pk=employee_id)

        open_attendance = {
            row.user_id: row
            for row in AttendanceRecord.objects.filter(
                tenant=tenant,
                user_id__in=users.values_list("id", flat=True),
                check_out__isnull=True,
            ).order_by("-check_in", "-id")
        }

        latest_shot_by_user = {}
        shots = ScreenshotRecord.objects.filter(
            tenant=tenant,
            user_id__in=users.values_list("id", flat=True),
        ).select_related("user").order_by("user_id", "-captured_at", "-id")
        for shot in shots:
            if shot.user_id not in latest_shot_by_user:
                latest_shot_by_user[shot.user_id] = shot

        payload = []
        for u in users:
            shot = latest_shot_by_user.get(u.id)
            attendance = open_attendance.get(u.id)
            is_online = attendance is not None
            screenshot_is_live = bool(
                shot
                and is_online
                and shot.captured_at
                and shot.captured_at >= live_cutoff
            )
            stale_reason = None
            if not shot:
                stale_reason = "No screenshot yet"
            elif not is_online:
                stale_reason = "Offline"
            elif shot.captured_at < live_cutoff:
                stale_reason = "Screenshot stale (30s+)"
            payload.append(
                {
                    "employee": {
                        "id": u.id,
                        "name": (u.name or "").strip() or u.email,
                        "email": u.email,
                    },
                    "status": "online" if is_online else "offline",
                    "last_activity": attendance.last_activity.isoformat() if attendance else None,
                    "latest_screenshot_at": shot.captured_at.isoformat() if shot and shot.captured_at else None,
                    "screenshot_is_live": screenshot_is_live,
                    "screenshot_reason": stale_reason,
                    "screenshot": (
                        {
                            "id": shot.id,
                            "captured_at": shot.captured_at.isoformat(),
                            "image_url": request.build_absolute_uri(shot.image.url) if shot.image else None,
                            "activity_status": shot.activity_status,
                        }
                        if screenshot_is_live
                        else None
                    ),
                }
            )
        return Response(payload)

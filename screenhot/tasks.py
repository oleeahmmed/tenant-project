import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import NamedTemporaryFile
import shutil
import tempfile

from django.conf import settings
from django.core.files import File
from django.db import transaction
from django.utils import timezone
from PIL import Image, UnidentifiedImageError

from screenhot.models import ScreenshotRecord, VideoJob

try:
    import imageio_ffmpeg
except Exception:  # pragma: no cover
    imageio_ffmpeg = None


_executor = ThreadPoolExecutor(max_workers=2)
_lock = threading.Lock()
_running_jobs = set()


def enqueue_video_job(job_id: int):
    with _lock:
        if job_id in _running_jobs:
            return
        _running_jobs.add(job_id)

    def _runner():
        try:
            generate_video_job(job_id)
        finally:
            with _lock:
                _running_jobs.discard(job_id)

    _executor.submit(_runner)


def _base_queryset(job: VideoJob):
    qs = ScreenshotRecord.objects.filter(
        tenant=job.tenant,
        user=job.target_user,
        captured_at__date__gte=job.date_from,
        captured_at__date__lte=job.date_to,
    )
    if job.time_from:
        qs = qs.filter(captured_at__time__gte=job.time_from)
    if job.time_to:
        qs = qs.filter(captured_at__time__lte=job.time_to)
    return qs.order_by("captured_at", "id")


def _make_video(frames, output_path: Path, fps: int):
    ffmpeg_path = getattr(settings, "SCREENHOT_FFMPEG_BINARY", "").strip()
    if not ffmpeg_path:
        if imageio_ffmpeg is not None:
            try:
                ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            except Exception:
                ffmpeg_path = ""
    if not ffmpeg_path:
        ffmpeg_path = shutil.which("ffmpeg") or ""

    if not ffmpeg_path:
        raise RuntimeError(
            "FFmpeg not found. Install 'imageio-ffmpeg' or add ffmpeg to PATH."
        )

    fps_value = str(max(int(fps), 1))

    with tempfile.TemporaryDirectory() as frame_dir:
        for i, frame in enumerate(frames):
            frame_path = Path(frame_dir) / f"frame_{i:06d}.jpg"
            frame.save(frame_path, "JPEG", quality=95)

        cmd = [
            ffmpeg_path,
            "-y",
            "-framerate",
            fps_value,
            "-i",
            str(Path(frame_dir) / "frame_%06d.jpg"),
            "-c:v",
            "libx264",
            "-profile:v",
            "baseline",
            "-level",
            "3.0",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-r",
            fps_value,
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(result.stderr[:1000] or "ffmpeg failed")


def generate_video_job(job_id: int):
    with transaction.atomic():
        job = VideoJob.objects.select_for_update().get(pk=job_id)
        if job.status not in (VideoJob.Status.PENDING, VideoJob.Status.FAILED):
            return
        job.status = VideoJob.Status.PROCESSING
        job.started_at = timezone.now()
        job.error_message = ""
        job.save(update_fields=["status", "started_at", "error_message", "updated_at"])

    job = VideoJob.objects.get(pk=job_id)
    screenshots = list(_base_queryset(job).values_list("image", flat=True))
    if not screenshots:
        job.status = VideoJob.Status.FAILED
        job.error_message = "No screenshots found in selected range."
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "error_message", "completed_at", "updated_at"])
        return

    loaded_frames = []
    try:
        for rel in screenshots:
            img_path = Path(settings.MEDIA_ROOT) / rel
            if not img_path.exists():
                continue
            try:
                with Image.open(img_path) as img:
                    loaded_frames.append(img.convert("RGB"))
            except (UnidentifiedImageError, OSError):
                continue

        if not loaded_frames:
            raise RuntimeError("No readable frames were found.")

        base_w, base_h = loaded_frames[0].size
        normalized = [frame.resize((base_w, base_h), Image.Resampling.LANCZOS) for frame in loaded_frames]
        with NamedTemporaryFile(suffix=".mp4", delete=True) as tmp:
            _make_video(normalized, Path(tmp.name), job.fps)
            tmp.seek(0)
            filename = f"screenhot-video-job-{job.pk}.mp4"
            job.output_file.save(filename, File(tmp), save=False)
            job.status = VideoJob.Status.COMPLETED
            job.completed_at = timezone.now()
            job.error_message = ""
            job.save(update_fields=["output_file", "status", "completed_at", "error_message", "updated_at"])
    except Exception as exc:
        job.status = VideoJob.Status.FAILED
        job.error_message = str(exc)[:4000]
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "error_message", "completed_at", "updated_at"])

from django.core.mail import send_mail
from django.conf import settings


def send_otp_email(email: str, otp_code: str):
    send_mail(
        subject="Your OTP Code",
        message=f"Your OTP is: {otp_code}\nValid for 10 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


def send_invitation_email(email: str, name: str, tenant_name: str, token: str, invite_url: str | None = None):
    invite_url = invite_url or f"{settings.FRONTEND_URL}/accept-invite?token={token}"
    send_mail(
        subject=f"You're invited to join {tenant_name}",
        message=(
            f"Hi {name},\n\n"
            f"You have been invited to join {tenant_name}.\n\n"
            f"Click the link below to set your password and activate your account:\n"
            f"{invite_url}\n\n"
            f"This link expires in 48 hours."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

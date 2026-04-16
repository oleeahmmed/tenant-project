import logging
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

logger = logging.getLogger(__name__)

_SHARE_SIGN_SALT = "vault.VaultSharedEntry"
# Upper bound for signed links; model `expires_at` is still enforced separately.
_MAX_SIGNATURE_AGE = 60 * 60 * 24 * 90


def vault_share_sign_token(share_pk: int) -> str:
    signer = TimestampSigner(salt=_SHARE_SIGN_SALT)
    return signer.sign(str(share_pk))


def vault_share_parse_token(token: str) -> int:
    signer = TimestampSigner(salt=_SHARE_SIGN_SALT)
    return int(signer.unsign(token, max_age=_MAX_SIGNATURE_AGE))


def vault_share_public_url(request, token: str) -> str:
    path = reverse("vault_public_share")
    return request.build_absolute_uri(f"{path}?{urlencode({'t': token})}")


def send_vault_share_invite_email(request, share) -> tuple[bool, str | None]:
    """
    Send invite with a time-limited signed link. Returns (success, error_message).
    """
    token = vault_share_sign_token(share.pk)
    link = vault_share_public_url(request, token)
    entry = share.entry
    tenant_name = share.tenant.name if share.tenant_id else ""
    shared_by = ""
    if share.shared_by_id:
        u = share.shared_by
        shared_by = (getattr(u, "get_full_name", lambda: "")() or "").strip() or getattr(u, "email", "") or str(u)

    subject = f"Shared credential: {entry.name}"
    if tenant_name:
        subject = f"[{tenant_name}] {subject}"

    context = {
        "share": share,
        "entry": entry,
        "link": link,
        "tenant_name": tenant_name,
        "shared_by_label": shared_by,
        "permission_label": share.get_permission_display(),
        "expires_at": share.expires_at,
    }
    plain = render_to_string("vault/email/share_invite.txt", context, request=request)
    html = render_to_string("vault/email/share_invite.html", context, request=request)

    try:
        send_mail(
            subject=subject,
            message=plain,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[share.shared_with_email],
            fail_silently=False,
            html_message=html,
        )
        return True, None
    except Exception as exc:
        logger.exception("vault share email failed for %s", share.shared_with_email)
        return False, str(exc)


def share_record_is_usable(share) -> bool:
    if not share.is_active:
        return False
    if share.expires_at and share.expires_at < timezone.now():
        return False
    return True

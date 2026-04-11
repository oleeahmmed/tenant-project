from typing import Tuple

from django.db import transaction

from auth_tenants.models import User

from .models import ChatMember, ChatRoom


def direct_key_for_users(a_id: int, b_id: int) -> str:
    lo, hi = (a_id, b_id) if a_id <= b_id else (b_id, a_id)
    return f"{lo}_{hi}"


@transaction.atomic
def get_or_create_direct_room(tenant, user_a: User, user_b: User) -> Tuple[ChatRoom, bool]:
    if user_a.pk == user_b.pk:
        raise ValueError("Cannot chat with yourself")
    key = direct_key_for_users(user_a.pk, user_b.pk)
    room, created = ChatRoom.objects.get_or_create(
        tenant=tenant,
        kind=ChatRoom.Kind.DIRECT,
        direct_key=key,
        defaults={"created_by": user_a},
    )
    if created:
        ChatMember.objects.bulk_create(
            [
                ChatMember(room=room, user=user_a),
                ChatMember(room=room, user=user_b),
            ]
        )
    else:
        ChatMember.objects.get_or_create(room=room, user=user_a)
        ChatMember.objects.get_or_create(room=room, user=user_b)
    return room, created


@transaction.atomic
def create_group_room(tenant, creator: User, title: str, member_ids: list[int]) -> ChatRoom:
    room = ChatRoom.objects.create(
        tenant=tenant,
        kind=ChatRoom.Kind.GROUP,
        title=title.strip()[:255],
        created_by=creator,
    )
    members = {creator.pk, *member_ids}
    ChatMember.objects.bulk_create(
        [ChatMember(room=room, user_id=uid, is_admin=(uid == creator.pk)) for uid in members]
    )
    return room

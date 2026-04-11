from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_room_message(room_id: int, payload: dict) -> None:
    """Push a message payload to all WebSocket subscribers of this room."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f"chat_{room_id}",
        {"type": "chat.message", "payload": payload},
    )

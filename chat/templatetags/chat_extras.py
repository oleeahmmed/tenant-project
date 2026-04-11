from django import template

register = template.Library()


@register.filter
def chat_title(room, user):
    if room is None or user is None:
        return ""
    return room.display_title(user)


@register.filter
def initials(name):
    if not name:
        return "?"
    return (name.strip()[:1] or "?").upper()


@register.filter
def msg_sidebar_preview(message, user):
    if message is None:
        return ""
    return message.sidebar_preview(user)

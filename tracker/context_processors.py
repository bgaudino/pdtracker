from django.contrib.messages import get_messages


def toasts_processor(request):
    toasts = [
        {"type": message.tags, "text": message.message}
        for message in get_messages(request)
    ]
    return {"toasts": toasts}

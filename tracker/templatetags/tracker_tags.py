from datetime import timedelta

from django import template

register = template.Library()


@register.filter
def duration(value):
    if not isinstance(value, timedelta):
        return value
    total_seconds = int(value.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    return f"{hours:02}:{minutes:02}"

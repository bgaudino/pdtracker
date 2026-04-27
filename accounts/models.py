from django.db import models
from django.utils import timezone

from authtools.models import AbstractEmailUser


class User(AbstractEmailUser):
    name = models.CharField(max_length=255, blank=True)

    def get_next_dose_message(self):
        cl = "Carbidopa/Levodopa"
        doses_today = self.medicationlog_set.filter(
            medication__name=cl, timestamp__date=timezone.now().date()
        ).count()
        if doses_today >= 3:
            return "Take your next dose when you wake up."

        last_dose = (
            self.medicationlog_set.filter(medication__name=cl)
            .order_by("-timestamp")
            .first()
        )
        if not last_dose:
            return

        window_start = last_dose.timestamp + timezone.timedelta(hours=5)
        window_end = last_dose.timestamp + timezone.timedelta(hours=6)
        now = timezone.now()
        fmt = "%I:%M %p"
        if now >= window_end:
            return "You can take your next dose now."
        elif now >= window_start:
            return f"Take your next dose between now and {window_end.strftime(fmt)}."
        else:
            return f"You can take your next dose between {window_start.strftime(fmt)} and {window_end.strftime(fmt)}."

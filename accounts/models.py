import hashlib
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

from authtools.models import AbstractEmailUser


class User(AbstractEmailUser):
    name = models.CharField(max_length=255, blank=True)

    def get_next_dose_message(self):
        now = timezone.localtime(timezone.now())
        cl = "Carbidopa/Levodopa"
        doses_today = self.medicationlog_set.filter(
            medication__name=cl, timestamp__date=now.date()
        ).count()
        if doses_today >= 3:
            return "Take your next dose when you wake up."

        last_dose = (
            self.medicationlog_set.filter(medication__name=cl)
            .order_by("-timestamp")
            .first()
        )
        if not last_dose:
            return "You can take your first dose now."

        taken_at = timezone.localtime(last_dose.timestamp)
        window_start = taken_at + timezone.timedelta(hours=5)
        window_end = taken_at + timezone.timedelta(hours=6)
        fmt = "%I:%M %p"
        if now >= window_end:
            return "You can take your next dose now."
        elif now >= window_start:
            return f"Take your next dose between now and {window_end.strftime(fmt)}."
        else:
            return f"You can take your next dose between {window_start.strftime(fmt)} and {window_end.strftime(fmt)}."


class ApiToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    token_hash = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return f"{self.name} ({self.user.email})"

    class Meta:
        unique_together = ("user", "name")

    def save(self, *args, **kwargs):
        if not self.token_hash:
            token = self.generate_token()
            self.token_hash = self.hash_token(token)
        super().save(*args, **kwargs)

    @classmethod
    def authenticate(cls, token):
        hash = cls().hash_token(token)
        try:
            instance = cls.objects.get(token_hash=hash)
        except cls.DoesNotExist:
            return None
        return instance.user

    def generate_token(self):
        return secrets.token_urlsafe(32)

    def hash_token(self, token):
        return hashlib.sha256(f"{settings.SECRET_KEY}:{token}".encode()).hexdigest()

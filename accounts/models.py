from django.db import models

from authtools.models import AbstractEmailUser


class User(AbstractEmailUser):
    name = models.CharField(max_length=255, blank=True)

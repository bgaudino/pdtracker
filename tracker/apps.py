from django import apps


class TrackerConfig(apps.AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tracker"

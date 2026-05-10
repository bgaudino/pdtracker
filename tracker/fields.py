from django.db import models


class Severity(models.IntegerChoices):
    NORMAL = 0, "Normal"
    SLIGHT = 1, "Slight"
    MILD = 2, "Mild"
    MODERATE = 3, "Moderate"
    SEVERE = 4, "Severe"


class SeverityField(models.IntegerField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("choices", Severity.choices)
        kwargs.setdefault("default", Severity.NORMAL)
        super().__init__(*args, **kwargs)

from django.db import models


class Severity(models.IntegerChoices):
    NONE = 0, "None"
    MILD = 1, "Mild"
    MILD_MODERATE = 2, "Mild-Moderate"
    MODERATE = 3, "Moderate"
    MODERATE_SEVERE = 4, "Moderate-Severe"
    SEVERE = 5, "Severe"


class SeverityField(models.IntegerField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("choices", Severity.choices)
        kwargs.setdefault("default", Severity.NONE)
        super().__init__(*args, **kwargs)

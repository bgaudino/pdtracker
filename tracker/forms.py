from django import forms

from .models import (
    CheckIn,
    ExerciseDystonia,
    HealthMetric,
    MedicationLog,
    TappingTest,
    TypingTest,
)
from .utils import camel_to_title, camel_to_snake


class BaseLogForm(forms.ModelForm):
    class Media:
        css = {
            "all": ("https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css",)
        }
        js = ("https://cdn.jsdelivr.net/npm/flatpickr", "js/datetime-picker.js")

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        if (
            not self.instance.pk
            and self._meta.model.objects.filter(
                user=self.user, timestamp=cleaned_data.get("timestamp")
            ).exists()
        ):
            raise forms.ValidationError(
                "You have already logged an entry for this timestamp."
            )
        return cleaned_data


class CheckInForm(BaseLogForm):
    class Meta:
        model = CheckIn
        fields = [
            "fatigue",
            "pain",
            "rigidity",
            "bradykinesia",
            "tremor",
            "hand_dysfunction",
            "notes",
            "timestamp",
        ]


class MedicationLogForm(BaseLogForm):
    class Meta:
        model = MedicationLog
        fields = ["medication", "timestamp"]

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, user=user, **kwargs)
        self.fields["medication"].queryset = user.medication_set.all()
        self.fields["medication"].empty_label = None


class TappingTestForm(BaseLogForm):
    class Meta:
        model = TappingTest
        fields = ["taps", "duration", "timestamp"]


class TypingTestForm(BaseLogForm):
    class Meta:
        model = TypingTest
        fields = ["prompt", "typed", "time_seconds", "timestamp"]


class HealthMetricForm(forms.Form):
    data_type = forms.ChoiceField()

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        data_types = (
            HealthMetric.objects.filter(user=user)
            .distinct("data_type")
            .order_by("data_type")
            .values_list("data_type", flat=True)
        )
        self.fields["data_type"].choices = [
            (camel_to_snake(dt), camel_to_title(dt)) for dt in data_types
        ]


class ExerciseDystoniaForm(forms.ModelForm):
    class Meta:
        model = ExerciseDystonia
        fields = ["onset_minutes", "severity", "notes"]

from django import forms

from .models import ActivityLog, CheckIn, MedicationLog, TappingTest, TypingTest


class BaseLogForm(forms.ModelForm):
    timestamp = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user


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


class ActivityLogForm(BaseLogForm):
    class Meta:
        model = ActivityLog
        fields = [
            "activity",
            "duration_minutes",
            "notes",
            "timestamp",
            "dystonia_present",
            "dystonia_severity",
            "dystonia_onset",
        ]

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, user=user, **kwargs)
        self.fields["activity"].queryset = user.activity_set.all()


class MedicationLogForm(BaseLogForm):
    class Meta:
        model = MedicationLog
        fields = ["medication", "timestamp"]

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, user=user, **kwargs)
        self.fields["medication"].queryset = user.medication_set.all()


class TappingTestForm(BaseLogForm):
    class Meta:
        model = TappingTest
        fields = ["taps", "duration", "timestamp"]


class TypingTestForm(BaseLogForm):
    class Meta:
        model = TypingTest
        fields = ["prompt", "typed", "time_seconds", "timestamp"]

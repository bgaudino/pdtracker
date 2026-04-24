from django.conf import settings
from django.db import models

from .fields import SeverityField


class Medication(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField()
    dose = models.CharField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.dose})"

    class Meta:
        unique_together = ("user", "name", "dose")


class Activity(models.Model):
    class Focus(models.TextChoices):
        AEROBIC = "aerobic", "Aerobic"
        STRENGTH = "strength", "Strength"
        MOBILITY = "mobility", "Mobility"
        BALANCE = "balance", "Balance"
        HYBRID = "hybrid", "Hybrid"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField()
    focus = models.CharField(choices=Focus.choices)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ("user", "name")
        verbose_name_plural = "activities"


class LogQuerySet(models.QuerySet):
    def with_last_dose(self):
        last_dose_subquery = (
            MedicationLog.objects.filter(
                user=models.OuterRef("user"),
                timestamp__lte=models.OuterRef("timestamp"),
            )
            .order_by("-timestamp")
            .values("timestamp")[:1]
        )
        return self.annotate(last_dose_at=models.Subquery(last_dose_subquery))

    def with_time_since_dose(self):
        return self.with_last_dose().annotate(
            time_since_dose=models.ExpressionWrapper(
                models.F("timestamp") - models.F("last_dose_at"),
                output_field=models.DurationField(),
            )
        )

    def group_by_hours_since_dose(self):
        queryset = self.with_time_since_dose().exclude(time_since_dose__isnull=True)
        groups = {}
        for obj in queryset:
            delta_hours = int(obj.time_since_dose.total_seconds() // 3600)
            delta_hours = min(delta_hours, 3)
            groups.setdefault(delta_hours, []).append(obj)
        return groups


class AbstractLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()

    objects = LogQuerySet.as_manager()

    class Meta:
        abstract = True


class MedicationLog(AbstractLog):
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.medication} ({self.timestamp})"


class CheckInQuerySet(LogQuerySet):
    def report(self):
        def average(lst):
            return sum(lst) / len(lst) if lst else 0

        groups = self.group_by_hours_since_dose()
        report_data = {}
        for hours, logs in groups.items():
            data = {
                attr: average([getattr(log, attr) for log in logs])
                for attr in [
                    "pain",
                    "rigidity",
                    "bradykinesia",
                    "tremor",
                    "hand_dysfunction",
                    "fatigue",
                ]
            }
            data["count"] = len(logs)
            report_data[hours] = data
        return report_data


class CheckIn(AbstractLog):
    notes = models.TextField(blank=True)
    pain = SeverityField()
    rigidity = SeverityField()
    bradykinesia = SeverityField()
    tremor = SeverityField()
    hand_dysfunction = SeverityField()
    fatigue = SeverityField()

    objects = CheckInQuerySet.as_manager()

    def __str__(self):
        return f"Check-in ({self.timestamp})"


class ActivityLog(AbstractLog):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    duration_minutes = models.IntegerField(default=0)
    dystonia_present = models.BooleanField(default=False)
    dystonia_severity = SeverityField(null=True, blank=True)
    dystonia_onset = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.activity.name} ({self.timestamp})"


class TappingTestQuerySet(LogQuerySet):
    def report(self):
        def average(lst):
            return sum(lst) / len(lst) if lst else 0

        groups = self.group_by_hours_since_dose()
        report_data = {}
        for hours, logs in groups.items():
            data = {
                attr: average([getattr(log, attr) for log in logs])
                for attr in [
                    "taps",
                    "duration",
                    "taps_per_second",
                ]
            }
            data["count"] = len(logs)
            report_data[hours] = data
        return report_data


class TappingTest(AbstractLog):
    taps = models.PositiveIntegerField()
    duration = models.PositiveIntegerField()

    objects = TappingTestQuerySet.as_manager()

    def __str__(self):
        return f"Tapping Test {self.taps} taps at {self.timestamp})"

    @property
    def taps_per_second(self):
        if self.duration > 0:
            return self.taps / self.duration
        return 0

from django.conf import settings
from django.db import models
from django.db.models.functions import Length
from django.urls import reverse
from django.utils import timezone

from .fields import SeverityField
from .utils import average


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
    def recent(self, as_of=None):
        now = timezone.localtime(timezone.now())
        if as_of is None:
            as_of = now - timezone.timedelta(days=14)
        return self.filter(timestamp__gte=as_of, timestamp__lte=now).order_by(
            "-timestamp"
        )

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
            delta_hours = min(delta_hours, 5)
            groups.setdefault(delta_hours, []).append(obj)
        return groups

    def report(self, fields):
        groups = self.group_by_hours_since_dose()
        report_data = {}
        for hours, logs in sorted(groups.items()):
            data = {
                field: average([getattr(log, field) for log in logs])
                for field in fields
            }
            data["count"] = len(logs)
            report_data[hours] = data
        return report_data


class AbstractLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()

    objects = LogQuerySet.as_manager()

    class Meta:
        abstract = True
        ordering = ["-timestamp"]

    @classmethod
    def breadcrumbs(cls):
        model_name = cls._meta.model_name
        return [
            {"name": "Home", "url": reverse("home")},
            {
                "name": f"{cls._meta.verbose_name_plural.title()}",
                "url": reverse(f"{model_name}-list"),
            },
            {"name": "New", "url": reverse(f"{model_name}-create")},
        ]


class MedicationLog(AbstractLog):
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.medication} ({self.timestamp})"


class CheckIn(AbstractLog):
    notes = models.TextField(blank=True)
    pain = SeverityField()
    rigidity = SeverityField()
    bradykinesia = SeverityField()
    tremor = SeverityField()
    hand_dysfunction = SeverityField()
    fatigue = SeverityField()

    def __str__(self):
        return f"Check-in ({self.timestamp})"

    @property
    def overall_severity(self):
        return average(
            [
                self.pain,
                self.rigidity,
                self.bradykinesia,
                self.tremor,
                self.hand_dysfunction,
                self.fatigue,
            ]
        )


class ActivityLogQuerySet(LogQuerySet):
    def report(self):
        return list(
            self.recent()
            .filter(activity__name="Running")
            .values("dystonia_onset", "dystonia_severity")
        )


class ActivityLog(AbstractLog):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    duration_minutes = models.PositiveIntegerField(default=0)
    dystonia_severity = SeverityField()
    dystonia_onset = models.PositiveSmallIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(duration_minutes__gte=0),
                name="duration_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(dystonia_severity__gte=0),
                name="dystonia_severity_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(dystonia_onset__gte=0),
                name="dystonia_onset_non_negative",
            ),
            models.CheckConstraint(
                condition=~models.Q(dystonia_onset__gt=0, dystonia_severity=0),
                name="dystonia_onset_without_severity",
            ),
        ]

    objects = ActivityLogQuerySet.as_manager()

    def __str__(self):
        return f"{self.activity.name} ({self.timestamp})"

    @property
    def dystonia_present(self):
        return bool(self.dystonia_severity)


class TappingTest(AbstractLog):
    taps = models.PositiveIntegerField()
    duration = models.PositiveIntegerField()

    def __str__(self):
        return f"Tapping Test {self.taps} taps at {self.timestamp})"

    @property
    def taps_per_second(self):
        if self.duration > 0:
            return self.taps / self.duration
        return 0


correct_expr = models.Func(
    models.F("prompt"),
    models.F("typed"),
    function="count_correct_chars",
)

typed_len = Length("typed")


class TypingTest(AbstractLog):
    prompt = models.TextField()
    typed = models.TextField()
    time_seconds = models.DecimalField(max_digits=6, decimal_places=2)
    correct_chars = models.GeneratedField(
        expression=correct_expr,
        output_field=models.IntegerField(),
        db_persist=True,
    )
    errors = models.GeneratedField(
        expression=typed_len - correct_expr,
        output_field=models.IntegerField(),
        db_persist=True,
    )
    accuracy = models.GeneratedField(
        expression=models.Case(
            models.When(typed="", then=0),
            default=(correct_expr * 100.0) / typed_len,
            output_field=models.DecimalField(max_digits=5, decimal_places=2),
        ),
        output_field=models.DecimalField(max_digits=5, decimal_places=2),
        db_persist=True,
    )
    wpm = models.GeneratedField(
        expression=(correct_expr / 5.0) / (models.F("time_seconds") / 60.0),
        output_field=models.DecimalField(max_digits=5, decimal_places=2),
        db_persist=True,
    )

    def __str__(self):
        return f"Typing Test {self.wpm} WPM at {self.timestamp})"

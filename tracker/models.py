from collections import OrderedDict
from django.conf import settings
from django.db import models
from django.db.models.functions import Length
from django.urls import reverse
from django.utils import timezone

from .fields import SeverityField
from .utils import average, camel_to_title


class Medication(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField()
    dose = models.CharField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.dose})"

    class Meta:
        unique_together = ("user", "name", "dose")


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

    def group_by_time_of_day(self):
        queryset = self.exclude(timestamp__isnull=True)
        morning, afternoon, evening, night = [], [], [], []
        for obj in queryset:
            hour = timezone.localtime(obj.timestamp).hour
            if hour >= 22 or hour < 6:
                night.append(obj)
            elif 6 <= hour < 12:
                morning.append(obj)
            elif 12 <= hour < 18:
                afternoon.append(obj)
            else:
                evening.append(obj)
        return {
            "morning": morning,
            "afternoon": afternoon,
            "evening": evening,
            "night": night,
        }

    def report(self, fields, groups=None):
        sort = False
        if groups is None:
            groups = self.group_by_hours_since_dose()
            sort = True
        report_data = {}
        items = sorted(groups.items()) if sort else groups.items()
        for hours, logs in items:
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
        unique_together = [
            ("user", "timestamp"),
        ]

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
    overall_severity = models.GeneratedField(
        expression=average(
            [
                models.F("pain"),
                models.F("rigidity"),
                models.F("bradykinesia"),
                models.F("tremor"),
                models.F("hand_dysfunction"),
                models.F("fatigue"),
            ]
        ),
        output_field=models.DecimalField(max_digits=4, decimal_places=2),
        db_persist=True,
    )

    def __str__(self):
        return f"Check-in ({self.timestamp})"

    @property
    def overall_severity_display(self):
        from .fields import Severity

        return Severity(round(self.overall_severity)).label


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


class Workout(AbstractLog):
    activity_type = models.CharField()
    data = models.JSONField(default=dict)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Workout: {self.activity_type} ({self.timestamp})"

    @classmethod
    def from_json(cls, user, data):
        workouts = [
            cls(
                user=user,
                timestamp=workout["startDate"],
                activity_type=workout["activityType"],
                data=workout,
            )
            for workout in data.get("workouts", [])
        ]
        return cls.objects.bulk_create(
            workouts,
            update_conflicts=True,
            unique_fields=["user", "timestamp"],
            update_fields=["data"],
        )

    @classmethod
    def breadcrumbs(cls):
        return [
            {"name": "Home", "url": reverse("home")},
            {"name": "Workouts", "url": reverse("workout-list")},
        ]

    @property
    def activity_type_display(self):
        return camel_to_title(self.activity_type)

    @property
    def statistics(self):
        return self.data.get("statistics", {})

    @property
    def heart_rate(self):
        return self.statistics.get("HKQuantityTypeIdentifierHeartRate", {})

    @property
    def duration(self):
        seconds = self.data.get("duration", 0)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{int(hours)}:{int(minutes):02}:{int(seconds):02}"
        return f"{int(minutes)}:{int(seconds):02}"

    @property
    def steps(self):
        return self.statistics.get("HKQuantityTypeIdentifierStepCount", {}).get("sum")

    @property
    def distance(self):
        return self.statistics.get(
            "HKQuantityTypeIdentifierDistanceWalkingRunning", {}
        ).get("sum", 0)

    @property
    def distance_km(self):
        return self.distance / 1000

    @property
    def distance_miles(self):
        return self.distance / 1609.34

    @property
    def pace_km(self):
        return self._pace(self.distance_km)

    @property
    def pace_miles(self):
        return self._pace(self.distance_miles)

    def _pace(self, distance):
        duration = self.data.get("duration", 0)
        if not (duration and distance):
            return
        total_minutes = duration / 60
        pace = total_minutes / distance
        minutes = int(pace)
        seconds = int((pace - minutes) * 60)
        return f"{minutes}:{seconds:02} per {'km' if distance == self.distance_km else 'mile'}"


class HealthMetric(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    data_type = models.CharField()
    value = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField()
    date = models.DateField()

    class Meta:
        ordering = ["data_type", "-date"]
        unique_together = ("user", "data_type", "date")

    def __str__(self):
        return f"{self.data_type}: {self.value} {self.unit} at {self.date}"

    @classmethod
    def from_json(cls, user, data):
        data_types = data.get("exportInfo", {}).get("dataTypes", [])
        health_metrics = []
        for data_type in data_types:
            for metric in data[data_type]:
                health_metrics.append(
                    HealthMetric(
                        user=user,
                        date=metric["date"],
                        data_type=data_type,
                        value=metric["value"],
                        unit=metric["unit"],
                    )
                )
        return HealthMetric.objects.bulk_create(
            health_metrics,
            update_conflicts=True,
            unique_fields=["user", "date", "data_type"],
            update_fields=["value", "unit"],
        )


class ExerciseDystonia(models.Model):
    workout = models.OneToOneField(
        Workout, on_delete=models.CASCADE, limit_choices_to={"activity_type": "running"}
    )
    onset_minutes = models.PositiveSmallIntegerField()
    severity = SeverityField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Dystonia details for {self.workout}"

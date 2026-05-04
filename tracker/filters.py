from django.db.models import F
import django_filters

from .utils import camel_to_title


class NullsLastOrderingFilter(django_filters.OrderingFilter):
    def filter(self, qs, value):
        if not value:
            return qs

        ordering = []
        for param in value:
            descending = param.startswith("-")
            field = self.get_ordering_value(param)
            field = field[1:] if descending else field

            if descending:
                ordering.append(F(field).desc(nulls_last=True))
            else:
                ordering.append(F(field).asc(nulls_last=True))

        return qs.order_by(*ordering)


class CheckInFilter(django_filters.FilterSet):
    order = NullsLastOrderingFilter(
        fields=(
            "timestamp",
            "time_since_dose",
            "overall_severity",
            "pain",
            "fatigue",
            "rigidity",
            "bradykinesia",
            "tremor",
            "hand_dysfunction",
        )
    )


class TappingTestFilter(django_filters.FilterSet):
    order = NullsLastOrderingFilter(
        fields=(
            "timestamp",
            "time_since_dose",
            "taps",
        )
    )


class TypingTestFilter(django_filters.FilterSet):
    order = NullsLastOrderingFilter(
        fields=(
            "timestamp",
            "time_since_dose",
            "wpm",
            "accuracy",
        )
    )


class WorkoutFilter(django_filters.FilterSet):
    activity_type = django_filters.ChoiceFilter(
        field_name="activity_type", lookup_expr="iexact", empty_label="All"
    )
    order = NullsLastOrderingFilter(
        fields=(
            "timestamp",
            "time_since_dose",
            "duration",
            "activity_type",
            ("data__duration", "duration"),
            (
                "data__statistics__HKQuantityTypeIdentifierHeartRate__average",
                "average_heart_rate",
            ),
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.request and self.request.user.is_authenticated:
            activity_types = (
                self.request.user.workout_set.order_by("activity_type")
                .values_list("activity_type", flat=True)
                .distinct()
            )
            self.filters["activity_type"].extra["choices"] = [
                [activity_type, camel_to_title(activity_type)]
                for activity_type in activity_types
            ]
        self.form.fields["order"].widget.attrs["hidden"] = True

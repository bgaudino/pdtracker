from django.db.models import F
import django_filters


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
            "taps_per_second",
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

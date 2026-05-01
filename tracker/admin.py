from django.contrib import admin

from . import models


@admin.register(models.CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Medication)
class MedicationAdmin(admin.ModelAdmin):
    pass


@admin.register(models.MedicationLog)
class MedicationLogAdmin(admin.ModelAdmin):
    pass


@admin.register(models.TappingTest)
class TappingTestAdmin(admin.ModelAdmin):
    pass


@admin.register(models.TypingTest)
class TypingTestAdmin(admin.ModelAdmin):
    readonly_fields = (
        "user",
        "timestamp",
        "prompt",
        "typed",
        "time_seconds",
        "correct_chars",
        "errors",
        "accuracy",
        "wpm",
    )


class ExerciseDystoniaInline(admin.TabularInline):
    model = models.ExerciseDystonia
    extra = 0


@admin.register(models.Workout)
class WorkoutAdmin(admin.ModelAdmin):
    readonly_fields = ("user", "timestamp", "activity_type", "data")
    inlines = [ExerciseDystoniaInline]

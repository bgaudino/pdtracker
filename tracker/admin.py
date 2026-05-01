from django.contrib import admin

from . import models


@admin.register(models.Activity)
class ActivityAdmin(admin.ModelAdmin):
    pass


@admin.register(models.ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    pass


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


@admin.register(models.Workout)
class WorkoutAdmin(admin.ModelAdmin):
    readonly_fields = ("user", "timestamp", "activity_type", "data")

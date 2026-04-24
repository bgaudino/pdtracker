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

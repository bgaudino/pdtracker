from django.contrib import admin
from django.urls import include, path

from . import views

urlpatterns = [
    path("accounts/", include("django.contrib.auth.urls")),
    path("admin/", admin.site.urls),
    path("", views.HomeView.as_view(), name="home"),
    path("checkin/", views.CheckInCreateView.as_view(), name="checkin-create"),
    path(
        "medicationlog/",
        views.MedicationLogCreateView.as_view(),
        name="medicationlog-create",
    ),
    path(
        "activitylog/", views.ActivityLogCreateView.as_view(), name="activitylog-create"
    ),
    path(
        "medicationlogs/",
        views.MedicationLogListView.as_view(),
        name="medicationlog-list",
    ),
    path("checkins/", views.CheckInListView.as_view(), name="checkin-list"),
    path("activitylogs/", views.ActivityLogListView.as_view(), name="activitylog-list"),
    path("reports/", views.ReportsView.as_view(), name="reports"),
]

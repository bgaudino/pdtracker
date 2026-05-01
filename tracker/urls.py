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
        "medicationlogs/",
        views.MedicationLogListView.as_view(),
        name="medicationlog-list",
    ),
    path("checkins/", views.CheckInListView.as_view(), name="checkin-list"),
    path("reports/", views.ReportsView.as_view(), name="reports"),
    path(
        "tappingtest/", views.TappingTestCreateView.as_view(), name="tappingtest-create"
    ),
    path("tappingtests/", views.TappingTestListView.as_view(), name="tappingtest-list"),
    path("typingtest/", views.TypingTestCreateView.as_view(), name="typingtest-create"),
    path("typingtests/", views.TypingTestListView.as_view(), name="typingtest-list"),
    path("workouts/", views.WorkoutListView.as_view(), name="workout-list"),
    path(
        "workouts/<int:pk>/", views.WorkoutDetailView.as_view(), name="workout-detail"
    ),
    path("ai-analysis/", views.AIAnalysisView.as_view(), name="ai-analysis"),
    path(
        "apple-health-import/",
        views.AppleHealthImportView.as_view(),
        name="apple-health-import",
    ),
]

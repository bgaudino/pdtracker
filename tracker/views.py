import json
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Avg, DecimalField
from django.db.models.functions import Coalesce
from django.forms import model_to_dict
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    View,
)

from ai_chat import client
from ai_chat.prompts.models import SystemPrompt
import markdown
import nh3

from accounts.models import ApiToken
from .constants import TYPING_PROMPT
from .filters import CheckInFilter, TappingTestFilter, TypingTestFilter, WorkoutFilter
from .forms import (
    AppleHealthImportForm,
    CheckInForm,
    ExerciseDystoniaForm,
    HealthMetricForm,
    MedicationLogForm,
    TappingTestForm,
    TypingTestForm,
)
from .models import (
    CheckIn,
    HealthMetric,
    MedicationLog,
    TappingTest,
    TypingTest,
    Workout,
)
from .utils import camel_to_title, snake_to_camel


logger = logging.getLogger(__name__)


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dose_message"] = self.request.user.get_next_dose_message()
        return context


class BaseLogCreateView(LoginRequiredMixin, CreateView):
    template_name = "tracker/log_form.html"

    @property
    def model_name(self):
        return self.form_class._meta.model._meta.model_name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = f"New {self.form_class._meta.model._meta.verbose_name}"
        context["breadcrumbs"] = self.form_class._meta.model.breadcrumbs()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial["timestamp"] = timezone.now()
        return initial

    def get_success_url(self):
        return reverse(f"{self.model_name}-list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(
            self.request,
            f"{self.form_class._meta.model._meta.verbose_name.title()} saved successfully!",
        )
        return super().form_valid(form)


class CheckInCreateView(BaseLogCreateView):
    form_class = CheckInForm


class MedicationLogCreateView(BaseLogCreateView):
    form_class = MedicationLogForm


class TappingTestCreateView(BaseLogCreateView):
    form_class = TappingTestForm
    template_name = "tracker/tappingtest.html"


class TypingTestCreateView(BaseLogCreateView):
    form_class = TypingTestForm
    template_name = "tracker/typingtest.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["prompt"] = TYPING_PROMPT
        return context

    def get_initial(self):
        initial = super().get_initial()
        initial["prompt"] = " ".join(TYPING_PROMPT)
        return initial


class BaseLogListView(LoginRequiredMixin, ListView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = self.model.breadcrumbs()[:-1]
        return context

    def get_queryset(self):
        qs = (
            self.model.objects.filter(user=self.request.user)
            .recent()
            .with_time_since_dose()
        )
        if hasattr(self, "filterset_class"):
            self.filterset = self.filterset_class(
                self.request.GET, queryset=qs, request=self.request
            )
            return self.filterset.qs
        return qs


class CheckInListView(BaseLogListView):
    model = CheckIn
    filterset_class = CheckInFilter


class MedicationLogListView(BaseLogListView):
    model = MedicationLog

    def get_queryset(self):
        return super().get_queryset().select_related("medication")


class TappingTestListView(BaseLogListView):
    model = TappingTest
    filterset_class = TappingTestFilter


class TypingTestListView(BaseLogListView):
    model = TypingTest
    filterset_class = TypingTestFilter


class WorkoutListView(BaseLogListView):
    model = Workout
    filterset_class = WorkoutFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filterset.form
        context["breadcrumbs"] = self.model.breadcrumbs()
        return context


class WorkoutDetailView(LoginRequiredMixin, DetailView):
    model = Workout

    def get_form(self):
        dystonia = getattr(self.object, "exercisedystonia", None)
        data = self.request.POST if self.request.method == "POST" else None
        return ExerciseDystoniaForm(instance=dystonia, data=data)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = self.model.breadcrumbs() + [
            {"name": "Details", "url": ""},
        ]
        if context["object"].activity_type == "running":
            context["form"] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            dystonia = form.save(commit=False)
            dystonia.workout = self.object
            dystonia.save()
            return redirect("workout-detail", pk=self.object.pk)
        return self.render_to_response(self.get_context_data(form=form))

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(user=self.request.user)
            .select_related("exercisedystonia")
        )


def get_logs_for_user(user):
    check_ins = CheckIn.objects.filter(user=user).recent()
    tapping_tests = TappingTest.objects.filter(user=user).recent()
    typing_tests = TypingTest.objects.filter(user=user).recent()
    return check_ins, tapping_tests, typing_tests


def generate_reports(check_ins, tapping_tests, typing_tests):
    reports = {
        "checkin": check_ins.report(fields=["overall_severity"]),
        "tappingtest": tapping_tests.report(fields=["taps_per_second"]),
        "typingtest": typing_tests.report(fields=["wpm", "accuracy"]),
    }
    return reports


class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/reports.html"

    def get_context_data(self, **kwargs):
        check_ins, tapping_tests, typing_tests = get_logs_for_user(self.request.user)
        context = super().get_context_data(**kwargs)
        context["reports"] = generate_reports(check_ins, tapping_tests, typing_tests)
        context["reports"]["time_of_day"] = check_ins.report(
            fields=["overall_severity"], groups=check_ins.group_by_time_of_day()
        )
        context["breadcrumbs"] = [
            {"name": "Home", "url": reverse("home")},
            {"name": "Reports", "url": reverse("reports")},
        ]
        return context


class AIAnalysisView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/ai_analysis.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        system_prompt = SystemPrompt.objects.first()
        if not system_prompt:
            return context

        checkins, tapping_tests, typing_tests = get_logs_for_user(self.request.user)
        reports = generate_reports(checkins, tapping_tests, typing_tests)

        def format_logs(logs):
            message = (
                f"Here are the most recent {logs.model._meta.verbose_name_plural}:\n"
            )
            return message + ", ".join([str(model_to_dict(log)) for log in logs])

        try:
            response = client.chat(
                messages=[
                    {
                        "role": "user",
                        "content": f"Generate a report summarizing the following data: {reports}",
                    },
                    *[
                        {"role": "system", "content": format_logs(logs)}
                        for logs in [checkins, tapping_tests, typing_tests]
                    ],
                ],
                system_prompt=system_prompt.content,
            )
            message = "".join([message for message in response])
        except Exception as e:
            logger.error(f"Error generating AI report: {e}")
            context["ai_report"] = "Error generating AI report."
            return context

        html = markdown.markdown(message)
        context["ai_report"] = nh3.clean(html)
        return context


class HealthMetricSummaryView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/healthmetric_summary.html"

    def get_metrics(self, data_type):
        user = self.request.user
        qs = user.healthmetric_set.filter(data_type=data_type)
        today = timezone.now().date()
        two_weeks_ago = today - timezone.timedelta(days=14)
        two_week_qs = qs.filter(date__gte=two_weeks_ago, date__lt=today)
        latest = qs.order_by("-date").first()
        latest_value = latest.value if latest else None
        avg = two_week_qs.aggregate(
            avg_value=Coalesce(Avg("value"), 0, output_field=DecimalField())
        )["avg_value"]
        return {
            "latest": latest_value,
            "avg": avg,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumbs"] = [
            {"name": "Home", "url": reverse("home")},
            {"name": "Health Metrics", "url": ""},
        ]
        context["metrics"] = {
            dt: self.get_metrics(dt)
            for dt in (
                "stepCount",
                "exerciseMinutes",
                "vo2Max",
                "restingHeartRate",
                "weight",
                "dietaryProtein",
            )
        }
        return context


class HealthMetricListView(LoginRequiredMixin, ListView):
    model = HealthMetric
    allow_empty = False

    def setup(self, request, *args, **kwargs):
        self.slug = kwargs["data_type"]
        self.data_type = snake_to_camel(self.slug)
        return super().setup(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = camel_to_title(self.data_type)
        context["title"] = title
        context["breadcrumbs"] = [
            {"name": "Home", "url": reverse("home")},
            {"name": "Health Metrics", "url": reverse("healthmetric-summary")},
            {"name": f"{title} Metrics", "url": ""},
        ]
        context["data"] = [model_to_dict(metric) for metric in context["object_list"]]
        context["form"] = HealthMetricForm(
            user=self.request.user, initial={"data_type": self.slug}
        )
        return context

    def get_queryset(self):
        last_month = timezone.now().date() - timezone.timedelta(days=30)
        return (
            super()
            .get_queryset()
            .filter(
                user=self.request.user, data_type=self.data_type, date__gte=last_month
            )
            .order_by("date")
        )


@method_decorator(csrf_exempt, name="dispatch")
class AppleHealthImportApiView(View):
    def authenticate(self, request):
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None
        token = authorization.replace("Bearer ", "")
        return ApiToken.authenticate(token)

    def post(self, request, *args, **kwargs):
        user = self.authenticate(request)
        if not user:
            return HttpResponse("Unauthorized", status=401)

        data = json.loads(request.body)
        workouts = Workout.from_json(user, data)
        health_metrics = HealthMetric.from_json(user, data)
        message = "Successfully imported data from Apple Health."
        if workouts:
            message += f" Imported {len(workouts)} workouts."
        if health_metrics:
            message += f" Imported {len(health_metrics)} health metrics."
        return HttpResponse(message)


class AppleHealthFileImportView(LoginRequiredMixin, FormView):
    form_class = AppleHealthImportForm
    template_name = "tracker/healthmetric_import.html"

    def form_valid(self, form):
        user = self.request.user
        try:
            data = json.loads(form.cleaned_data["file"].read())
        except json.JSONDecodeError:
            form.add_error("file", "Invalid JSON file.")
            return self.form_invalid(form)
        try:
            self.workouts = Workout.from_json(user, data)
            if self.workouts:
                messages.success(
                    self.request,
                    f"Successfully imported {len(self.workouts)} workouts.",
                )
            self.health_metrics = HealthMetric.from_json(user, data)
            if self.health_metrics:
                messages.success(
                    self.request,
                    f"Successfully imported {len(self.health_metrics)} health metrics.",
                )
        except Exception as e:
            logger.error(f"Error importing Apple Health data: {e}")
            form.add_error("file", "Error importing data")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        if getattr(self, "workouts", None):
            return reverse("workout-list")
        if getattr(self, "health_metrics", None):
            return reverse("healthmetric-summary")
        return reverse("home")

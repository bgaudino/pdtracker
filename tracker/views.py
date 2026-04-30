import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import model_to_dict
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, ListView, TemplateView

from ai_chat import client
from ai_chat.prompts.models import SystemPrompt
import markdown
import nh3

from .constants import TYPING_PROMPT
from .forms import (
    ActivityLogForm,
    CheckInForm,
    MedicationLogForm,
    TappingTestForm,
    TypingTestForm,
)
from .models import ActivityLog, CheckIn, MedicationLog, TappingTest, TypingTest


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
        return super().form_valid(form)


class CheckInCreateView(BaseLogCreateView):
    form_class = CheckInForm


class MedicationLogCreateView(BaseLogCreateView):
    form_class = MedicationLogForm


class ActivityLogCreateView(BaseLogCreateView):
    form_class = ActivityLogForm


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
        return self.model.objects.filter(user=self.request.user).recent()


class CheckInListView(BaseLogListView):
    model = CheckIn


class MedicationLogListView(BaseLogListView):
    model = MedicationLog

    def get_queryset(self):
        return super().get_queryset().select_related("medication")


class ActivityLogListView(BaseLogListView):
    model = ActivityLog

    def get_queryset(self):
        return super().get_queryset().select_related("activity")


class TappingTestListView(BaseLogListView):
    model = TappingTest


class TypingTestListView(BaseLogListView):
    model = TypingTest


def get_logs_for_user(user):
    check_ins = CheckIn.objects.filter(user=user).recent()
    tapping_tests = TappingTest.objects.filter(user=user).recent()
    typing_tests = TypingTest.objects.filter(user=user).recent()
    activities = ActivityLog.objects.filter(
        user=user, activity__name="Running"
    ).recent()
    return check_ins, tapping_tests, typing_tests, activities


def generate_reports(check_ins, tapping_tests, typing_tests, activities):
    reports = {
        "checkin": check_ins.report(fields=["overall_severity"]),
        "tappingtest": tapping_tests.report(fields=["taps_per_second"]),
        "typingtest": typing_tests.report(fields=["wpm", "accuracy"]),
        "activitylog": activities.report(
            fields=["dystonia_onset", "dystonia_severity"]
        ),
    }
    return reports


class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/reports.html"

    def get_context_data(self, **kwargs):
        check_ins, tapping_tests, typing_tests, activities = get_logs_for_user(
            self.request.user
        )
        context = super().get_context_data(**kwargs)
        context["reports"] = generate_reports(
            check_ins, tapping_tests, typing_tests, activities
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

        checkins, tapping_tests, typing_tests, activities = get_logs_for_user(
            self.request.user
        )
        reports = generate_reports(checkins, tapping_tests, typing_tests, activities)

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
                        for logs in [checkins, tapping_tests, typing_tests, activities]
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

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, TemplateView

from .constants import TYPING_PROMPT
from .forms import (
    ActivityLogForm,
    CheckInForm,
    MedicationLogForm,
    TappingTestForm,
    TypingTestForm,
)
from .models import ActivityLog, CheckIn, MedicationLog, TappingTest, TypingTest


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dose_message"] = self.request.user.get_next_dose_message()
        return context


class BaseLogCreateView(LoginRequiredMixin, CreateView):
    success_url = reverse_lazy("home")
    template_name = "tracker/log_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = (
            f"Create {self.form_class._meta.model._meta.verbose_name}"
        )
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial["timestamp"] = timezone.now()
        return initial

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
    paginate_by = 100

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user).order_by("-timestamp")


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


class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/reports.html"

    def get_context_data(self, **kwargs):
        end = timezone.now()
        start = end - timezone.timedelta(days=14)
        reports = {}
        check_ins = CheckIn.objects.filter(
            user=self.request.user, timestamp__gte=start, timestamp__lt=end
        )
        reports["checkin"] = check_ins.report(
            fields=[
                "pain",
                "rigidity",
                "bradykinesia",
                "hand_dysfunction",
                "fatigue",
            ]
        )

        tapping_tests = TappingTest.objects.filter(
            user=self.request.user, timestamp__gte=start, timestamp__lt=end
        )
        reports["tappingtest"] = tapping_tests.report(fields=["taps_per_second"])

        typing_tests = TypingTest.objects.filter(
            user=self.request.user, timestamp__gte=start, timestamp__lt=end
        )
        reports["typingtest"] = typing_tests.report(fields=["wpm", "accuracy"])

        context = super().get_context_data(**kwargs)
        context["reports"] = reports

        return context

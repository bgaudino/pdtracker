from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, ListView, TemplateView

from .forms import ActivityLogForm, CheckInForm, MedicationLogForm
from .models import ActivityLog, CheckIn, MedicationLog


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "tracker/home.html"


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

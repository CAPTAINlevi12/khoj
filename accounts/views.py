from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import LogoutView as BaseLogoutView
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import RegistrationForm
from .mixins import RoleRequiredMixin
from .models import User


class RegisterView(CreateView):
    """Public sign-up. Always creates a FAMILY account (see forms.py)."""

    form_class = RegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        # CreateView.form_valid() normally just calls form.save() and
        # redirects. We call it ourselves so we get the saved User object
        # back, then log that user in immediately - nobody should have to
        # fill a password in twice, once to register and once to sign in.
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Account created. You're signed in.")
        return response


class LoginView(BaseLoginView):
    template_name = "accounts/login.html"


class LogoutView(BaseLogoutView):
    next_page = reverse_lazy("home")


class DashboardView(LoginRequiredMixin, TemplateView):
    """One URL for every signed-in user; the template shown depends on role.

    get_template_names() returns a *list*, tried in order until Django's
    template loader finds one that exists on disk. Here the list always has
    exactly one entry, but the mechanism is the same one that lets
    ListView fall back from "app/model_list.html" to a default.
    """

    def get_template_names(self):
        return [f"accounts/dashboard_{self.request.user.role.lower()}.html"]


class VerifierQueueView(RoleRequiredMixin, TemplateView):
    """Placeholder for Phase 5. Exists now so the role gate has something
    real to protect: this is the /verifier/queue/ the roadmap's "done when"
    test hand-types to confirm the wrong role gets a 403.
    """

    allowed_roles = [User.Role.VERIFIER, User.Role.ADMIN]
    template_name = "accounts/verifier_queue_placeholder.html"

from django.core.cache import cache
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from .models import Region
from .queries import get_primary_event


def get_stats():
    """Aggregate counts for the landing page, cached for five minutes.

    Four COUNT(*) queries on every anonymous page load would be four queries
    too many on the day this page is actually busy. cache.get_or_set runs the
    callable only on a miss.

    Reports, records and identifications are zero until Phases 2 to 4 create
    the models behind them. Zero is the honest number; inventing traffic on a
    page about missing people would be a lie with a particularly bad shape.
    """

    def compute():
        from .models import Organisation

        return {
            "reports": 0,
            "records": 0,
            "identified": 0,
            "facilities": Organisation.objects.filter(is_connected=True).count(),
        }

    return cache.get_or_set("landing_stats", compute, 300)


def home(request):
    """Public landing page.

    Four sections plus the telephone routes: what this is, whether it can
    help, what to do now. Everything explanatory is a link to one of the
    pages below, which have room the home page does not.
    """
    event = get_primary_event(request, "figures", "help_desks__region")

    return render(
        request,
        "registry/home.html",
        {"event": event, "stats": get_stats()},
    )


def how_it_works(request):
    """Why the registry is needed, how it works, and what helps a match."""
    return render(
        request,
        "registry/page_how_it_works.html",
        {"event": get_primary_event(request, "figures", "regions")},
    )


def matching(request):
    """The scoring demonstration.

    Needs the event because the demo's geography line follows
    Event.geography_rule — "downstream" is nonsense in an earthquake.
    """
    return render(
        request,
        "registry/page_matching.html",
        {"event": get_primary_event(request, "figures", "regions")},
    )


def coverage(request):
    """Which facilities take part, by district.

    "regions__organisations" follows the relation two levels deep in one
    extra query, which is what keeps this page flat however many districts
    the event covers.
    """
    event = get_primary_event(request, "figures", "regions__organisations")
    districts = event.regions.all() if event else Region.objects.none()

    return render(
        request,
        "registry/page_coverage.html",
        {"event": event, "districts": districts},
    )


def privacy(request):
    """What happens to what a family tells us."""
    return render(request, "registry/page_privacy.html", {})


def questions(request):
    """The FAQ, including the uncomfortable questions."""
    return render(request, "registry/page_questions.html", {})


# =====================================================================
# Phase 2 · missing-person reports
# =====================================================================

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import AppearanceForm, ContactForm, PhotoForm, WhereForm, WhoForm
from .models import MissingPersonReport

# The wizard is four ModelForms over one row, not four models. Each form
# lists only its own fields, so saving a later step cannot blank an earlier
# one. Four short screens survive an interrupted connection; a forty-field
# page does not.
STEP_FORMS = {1: WhoForm, 2: WhereForm, 3: AppearanceForm, 4: ContactForm}
STEP_LABELS = {1: _("Who"), 2: _("Where last seen"), 3: _("Appearance"), 4: _("Contact")}
LAST_STEP = 4


class OwnReportsMixin(LoginRequiredMixin):
    """Restrict every lookup to reports the signed-in user filed.

    This is the whole defence against IDOR, and the reason it lives in
    get_queryset() rather than in a permission check: the object is never
    fetched in the first place, so there is no window in which a view holds
    someone else's report and forgets to check. A stranger's id produces a
    404 from get_object_or_404 against this narrowed queryset — the same
    answer as an id that does not exist, which also avoids confirming that
    the report is real.

    Hiding the link would not have done this. Principle 7: ownership is
    enforced in the queryset, not the template.
    """

    model = MissingPersonReport

    def get_queryset(self):
        return MissingPersonReport.objects.filter(
            reporter=self.request.user
        ).prefetch_related("photos")


class ReportListView(OwnReportsMixin, ListView):
    """The family dashboard: your reports and their status."""

    template_name = "registry/report_list.html"
    context_object_name = "reports"


class ReportDetailView(OwnReportsMixin, DetailView):
    """One report, its status timeline, and its photographs."""

    template_name = "registry/report_detail.html"
    context_object_name = "report"


@login_required
def report_start(request):
    """Create the draft, then hand off to step 1.

    The row is written to the database immediately rather than held in the
    session, so a dead session, a closed browser or a flat battery does not
    destroy a half-finished report. That is why the wizard persists a DRAFT
    rather than using formtools' SessionWizardView.

    An untouched draft is reused instead of making a new one, so refreshing
    or coming back later continues where the person left off rather than
    littering their dashboard with empty rows.
    """
    event = get_primary_event(request)
    if event is None:
        messages.error(request, _("No disaster is currently loaded."))
        return redirect("home")

    draft = MissingPersonReport.objects.filter(
        reporter=request.user,
        status=MissingPersonReport.Status.DRAFT,
        full_name="",
    ).first()

    if draft is None:
        draft = MissingPersonReport.objects.create(
            reporter=request.user, event=event, full_name=""
        )

    return redirect("report-step", pk=draft.pk, step=1)


class ReportStepView(OwnReportsMixin, UpdateView):
    """One step of the wizard, chosen by the `step` URL argument."""

    template_name = "registry/report_step.html"
    context_object_name = "report"

    @property
    def step(self):
        return int(self.kwargs["step"])

    def get_form_class(self):
        return STEP_FORMS[self.step]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            step=self.step,
            steps=[(n, STEP_LABELS[n]) for n in STEP_FORMS],
            last_step=LAST_STEP,
            photo_form=PhotoForm(),
        )
        return context

    def form_valid(self, form):
        form.save()
        if "save_draft" in self.request.POST:
            messages.success(self.request, _("Saved. You can finish this later."))
            return redirect("report-detail", pk=self.object.pk)
        if self.step < LAST_STEP:
            return redirect("report-step", pk=self.object.pk, step=self.step + 1)
        return redirect("report-submit", pk=self.object.pk)


class ReportSubmitView(OwnReportsMixin, DetailView):
    """Turn a draft into a live search.

    Deliberately a POST: submitting changes state, and a state change must
    not be something a crawler or a prefetched link can trigger.
    """

    def post(self, request, *args, **kwargs):
        report = self.get_object()
        if report.status == MissingPersonReport.Status.DRAFT:
            report.status = MissingPersonReport.Status.SEARCHING
            report.save(update_fields=["status", "updated_at"])
            messages.success(
                request,
                _("Your report has been filed. You do not need to travel."),
            )
        return redirect("report-detail", pk=report.pk)

    def get(self, request, *args, **kwargs):
        # A confirmation screen, so the POST above is always deliberate.
        self.object = self.get_object()
        return render(
            request,
            "registry/report_submit.html",
            {"report": self.object},
        )


class ReportPhotoView(OwnReportsMixin, DetailView):
    """Attach one photograph to a report."""

    def post(self, request, *args, **kwargs):
        report = self.get_object()
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.report = report
            photo.save()
            messages.success(request, _("Photograph added."))
        else:
            messages.error(request, _("That file could not be read as an image."))
        return redirect("report-step", pk=report.pk, step=3)


class ReportWithdrawView(OwnReportsMixin, DetailView):
    """A family may withdraw a report at any time — a stated commitment."""

    def post(self, request, *args, **kwargs):
        report = self.get_object()
        report.status = MissingPersonReport.Status.WITHDRAWN
        report.save(update_fields=["status", "updated_at"])
        messages.success(request, _("Your report has been withdrawn."))
        return redirect("report-list")

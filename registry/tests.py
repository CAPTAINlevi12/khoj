"""Phase 2 tests.

The permission tests are the point of this file. Everything else in the
project can be re-derived by reading it; whether one family can read
another's report cannot be, and it is the failure that would matter most.
"""

from datetime import date

from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Event, MissingPersonReport


class ReportOwnershipTests(TestCase):
    """Phase 2's done-when test: IDOR, from every angle.

    setUpTestData runs once for the whole class and the rows are rolled back
    afterwards, which is why it is preferred over setUp for fixtures that no
    test mutates.
    """

    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.create(
            name="Test flood",
            slug="test-flood",
            kind=Event.Kind.FLOOD,
            occurred_on=date(2026, 8, 26),
            is_primary=True,
        )
        cls.owner = User.objects.create_user(
            username="owner", password="pw", role=User.Role.FAMILY
        )
        cls.stranger = User.objects.create_user(
            username="stranger", password="pw", role=User.Role.FAMILY
        )
        cls.report = MissingPersonReport.objects.create(
            reporter=cls.owner,
            event=cls.event,
            full_name="Ram Bahadur Tamang",
            status=MissingPersonReport.Status.SEARCHING,
        )

    def urls(self):
        pk = self.report.pk
        return {
            "detail": reverse("report-detail", args=[pk]),
            "step": reverse("report-step", args=[pk, 1]),
            "submit": reverse("report-submit", args=[pk]),
            "photo": reverse("report-photo", args=[pk]),
            "withdraw": reverse("report-withdraw", args=[pk]),
        }

    def test_owner_can_read_own_report(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.urls()["detail"]).status_code, 200)

    def test_stranger_gets_404_not_403_on_every_route(self):
        """404, not 403.

        403 would confirm the report exists, which leaks that a particular
        person has been reported missing. A stranger must not be able to tell
        an id that is taken from one that is free.
        """
        self.client.force_login(self.stranger)
        for name, url in self.urls().items():
            with self.subTest(route=name):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_stranger_cannot_post_to_any_route(self):
        """Writing is blocked as well as reading.

        The detail route answers 405 rather than 404 because DetailView
        rejects the method before it looks anything up. That is not a leak:
        the owner gets the same 405, so the response says nothing about
        whether the report exists.
        """
        write_routes = ["step", "submit", "photo", "withdraw"]
        urls = self.urls()

        self.client.force_login(self.stranger)
        for name in write_routes:
            with self.subTest(route=name):
                self.assertEqual(self.client.post(urls[name]).status_code, 404)

        # The one 405 is method-based, identical for owner and stranger.
        stranger_status = self.client.post(urls["detail"]).status_code
        self.client.force_login(self.owner)
        owner_status = self.client.post(urls["detail"]).status_code
        self.assertEqual(stranger_status, owner_status, "405 must not depend on ownership")

    def test_anonymous_is_redirected_to_login(self):
        for name, url in self.urls().items():
            with self.subTest(route=name):
                self.assertEqual(self.client.get(url).status_code, 302)

    def test_list_shows_only_own_reports(self):
        self.client.force_login(self.stranger)
        response = self.client.get(reverse("report-list"))
        self.assertNotContains(response, "Ram Bahadur Tamang")

    def test_stranger_cannot_change_state(self):
        """The important half: reading is blocked, and so is writing."""
        self.client.force_login(self.stranger)
        self.client.post(self.urls()["withdraw"])
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, MissingPersonReport.Status.SEARCHING)


class WizardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.event = Event.objects.create(
            name="Test flood",
            slug="test-flood",
            kind=Event.Kind.FLOOD,
            occurred_on=date(2026, 8, 26),
            is_primary=True,
        )
        cls.user = User.objects.create_user(
            username="family", password="pw", role=User.Role.FAMILY
        )

    def start(self):
        response = self.client.get(reverse("report-start"))
        return int(response.url.split("/")[2])

    def test_an_untouched_draft_is_reused(self):
        """Refreshing must not litter the dashboard with empty rows."""
        self.client.force_login(self.user)
        self.assertEqual(self.start(), self.start())
        self.assertEqual(MissingPersonReport.objects.count(), 1)

    def test_later_steps_do_not_blank_earlier_ones(self):
        """The reason each step is its own ModelForm with its own field list."""
        self.client.force_login(self.user)
        pk = self.start()

        self.client.post(reverse("report-step", args=[pk, 1]), {"full_name": "Kamala"})
        self.client.post(reverse("report-step", args=[pk, 3]), {"distinguishing_marks": "scar"})
        self.client.post(reverse("report-step", args=[pk, 4]), {"contact_phone": "98X"})

        report = MissingPersonReport.objects.get(pk=pk)
        self.assertEqual(report.full_name, "Kamala")
        self.assertEqual(report.distinguishing_marks, "scar")
        self.assertEqual(report.contact_phone, "98X")

    def test_blank_beats_guessed(self):
        """Every field except the name must accept being left empty."""
        self.client.force_login(self.user)
        pk = self.start()
        response = self.client.post(
            reverse("report-step", args=[pk, 1]),
            {"full_name": "Kamala", "age": "", "height_cm": ""},
        )
        self.assertEqual(response.status_code, 302)
        report = MissingPersonReport.objects.get(pk=pk)
        self.assertIsNone(report.age)
        self.assertIsNone(report.height_cm)

    def test_submitting_moves_draft_to_searching(self):
        self.client.force_login(self.user)
        pk = self.start()
        self.client.post(reverse("report-step", args=[pk, 1]), {"full_name": "Kamala"})
        self.client.post(reverse("report-submit", args=[pk]))

        report = MissingPersonReport.objects.get(pk=pk)
        self.assertEqual(report.status, MissingPersonReport.Status.SEARCHING)

    def test_submit_requires_post(self):
        """A GET returns the confirmation screen and changes nothing."""
        self.client.force_login(self.user)
        pk = self.start()
        self.client.get(reverse("report-submit", args=[pk]))
        report = MissingPersonReport.objects.get(pk=pk)
        self.assertEqual(report.status, MissingPersonReport.Status.DRAFT)

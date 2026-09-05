from django.db import models
from django.db.models import Q, UniqueConstraint
from django.utils.translation import gettext_lazy as _


class Region(models.Model):
    """An administrative area — a province, a district, a municipality.

    `parent` is a ForeignKey to "self", which is how you model a tree in one
    table: every row optionally points at another row of the same model. That
    is what lets one model cover any country's hierarchy instead of hardcoding
    Nepal's. Nepal is Province -> District -> Municipality; Türkiye is
    il -> ilçe. Same table, different depth.
    """

    class Kind(models.TextChoices):
        COUNTRY = "COUNTRY", _("Country")
        PROVINCE = "PROVINCE", _("Province")
        DISTRICT = "DISTRICT", _("District")
        MUNICIPALITY = "MUNICIPALITY", _("Municipality")

    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.DISTRICT)

    # PROTECT, not CASCADE: deleting a district must never silently delete
    # every municipality inside it.
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
    )

    # Optional geometry so the coverage map is data, not a constant in a
    # template. map_path is an SVG path in the event's own 420x250 viewBox.
    map_path = models.TextField(blank=True)
    label_x = models.PositiveSmallIntegerField(null=True, blank=True)
    label_y = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Event(models.Model):
    """A single disaster the registry is running for.

    Khoj is a registry for sudden-onset disasters that currently has one
    event loaded. Deploying it for an earthquake elsewhere is a new row, not
    a new codebase.
    """

    class Kind(models.TextChoices):
        FLOOD = "FLOOD", _("Flood")
        EARTHQUAKE = "EARTHQUAKE", _("Earthquake")
        LANDSLIDE = "LANDSLIDE", _("Landslide")
        GLACIER_COLLAPSE = "GLACIER_COLLAPSE", _("Glacier collapse")
        FIRE = "FIRE", _("Fire")
        CYCLONE = "CYCLONE", _("Cyclone")

    class Status(models.TextChoices):
        PREPARING = "PREPARING", _("Preparing")
        ACTIVE = "ACTIVE", _("Active")
        CLOSED = "CLOSED", _("Closed")

    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PREPARING)
    occurred_on = models.DateField()

    # One line the landing page can state plainly. Not marketing copy.
    summary = models.TextField(blank=True)

    regions = models.ManyToManyField(Region, related_name="events", blank=True)

    # Set once, when identification work genuinely finishes — which is months
    # or years after recovery ends, not when the news coverage stops.
    closed_on = models.DateField(null=True, blank=True)

    # The route for people who cannot use the website at all. Per-event,
    # because a different deployment answers a different telephone.
    hotline_phone = models.CharField(max_length=32, blank=True)
    hotline_hours = models.CharField(max_length=120, blank=True)

    # auto_now=True means Django overwrites this with "now" on every save().
    # Note that it is a *field*, not a property: it is stored, so it can be
    # ordered and filtered on, unlike something computed in Python.
    updated_at = models.DateTimeField(auto_now=True)

    # Which second calendar this deployment's readers expect beside the
    # Gregorian date. Nepal reads Bikram Sambat; Türkiye does not, and
    # printing BS dates there would be nonsense.
    class Calendar(models.TextChoices):
        NONE = "NONE", _("Gregorian only")
        BIKRAM_SAMBAT = "BIKRAM_SAMBAT", _("Bikram Sambat and Gregorian")

    secondary_calendar = models.CharField(
        max_length=20, choices=Calendar.choices, default=Calendar.NONE
    )

    # The event the bare landing page describes when it has to pick one.
    # Several events can be ACTIVE at once — a country can have two disasters
    # — so "active" cannot double as "the one to show".
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["-occurred_on"]
        constraints = [
            # A partial unique index: at most one PRIMARY event at a time.
            # Postgres enforces uniqueness only over rows matching the
            # condition, which is why this needs a real database, not SQLite.
            UniqueConstraint(
                fields=["is_primary"],
                condition=Q(is_primary=True),
                name="only_one_primary_event",
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def data_updated_at(self):
        """When the data behind this event last changed.

        The landing page stamps itself so a visitor can tell a live service
        from an abandoned one — which means this must reflect real activity,
        not the moment the page was rendered. "Now" on every request would be
        a freshness signal that is true even for a dead site, which is the
        same lie as a frozen date pointing the other way.

        Right now only the event row itself carries a timestamp. Phases 2 and
        3 fold in the newest report and record, and this is where that goes:
        max(self.updated_at, latest report, latest record).
        """
        return self.updated_at

    @property
    def geography_rule(self):
        """Which rule scores the 15 geography points for this kind of event.

        The engine's rule — "the recovery point must be downstream of the
        last-seen point, because water goes one way" — is FLOOD logic. In an
        earthquake nothing drifts and proximity is the whole signal; in a
        landslide it is downslope. Phase 4's scoring module reads this to pick
        a strategy, which is why `kind` is a behaviour switch and not a label.
        """
        return {
            self.Kind.FLOOD: "downstream",
            self.Kind.GLACIER_COLLAPSE: "downstream",
            self.Kind.LANDSLIDE: "downslope",
            self.Kind.EARTHQUAKE: "proximity",
            self.Kind.FIRE: "proximity",
            self.Kind.CYCLONE: "proximity",
        }.get(self.kind, "proximity")


class Organisation(models.Model):
    """A hospital, morgue, police post or army camp holding remains.

    Responders belong to one of these, and it is what scopes their queryset
    in Phase 3 — a nurse in Pokhara has no business reading Chitwan's records.
    """

    class Kind(models.TextChoices):
        HOSPITAL = "HOSPITAL", _("Hospital")
        MORGUE = "MORGUE", _("Morgue")
        POLICE_POST = "POLICE_POST", _("Police post")
        ARMY_CAMP = "ARMY_CAMP", _("Army camp")
        NGO = "NGO", _("Relief organisation")

    name = models.CharField(max_length=160)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.HOSPITAL)
    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name="organisations",
    )
    is_connected = models.BooleanField(default=True)
    contact_phone = models.CharField(max_length=32, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def record_count(self):
        """Unidentified records this organisation holds.

        Zero until Phase 3 creates UnidentifiedRecord; it becomes a reverse
        relation count then. Zero is the honest number in the meantime.
        """
        return 0


class EventFigure(models.Model):
    """One cited figure describing what went wrong in this event.

    The "without a registry" band is the case study, and every deployment has
    a different one. Storing the figures as rows keeps them citable and keeps
    invented numbers out: each carries the source it came from.
    """

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="figures")
    value = models.CharField(max_length=32)
    label = models.CharField(max_length=200)
    source = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.value} {self.label}"


class HelpDesk(models.Model):
    """A physical place a person can walk into and have a report filed for them.

    This is the population Google Person Finder lost in Pakistan in 2010 — the
    people with no connection at all — so it is data the system carries, not a
    line typed into a template.
    """

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="help_desks")
    name = models.CharField(max_length=160)
    region = models.ForeignKey(
        Region,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="help_desks",
    )
    phone = models.CharField(max_length=32, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


# Shared vocabulary. MissingPersonReport and UnidentifiedRecord must describe
# a person in the SAME words, or the matching engine has nothing to compare.
# Defining these once is what makes that guarantee structural rather than a
# thing someone has to remember.
class Sex(models.TextChoices):
    MALE = "MALE", _("Male")
    FEMALE = "FEMALE", _("Female")
    OTHER = "OTHER", _("Other")
    UNKNOWN = "UNKNOWN", _("Not known")


class Build(models.TextChoices):
    SLIGHT = "SLIGHT", _("Slight")
    MEDIUM = "MEDIUM", _("Medium")
    HEAVY = "HEAVY", _("Heavy")
    UNKNOWN = "UNKNOWN", _("Not known")


class MissingPersonReport(models.Model):
    """The family's side: one person someone is looking for.

    Almost every field is optional, and that is a domain decision rather than
    laziness — principle 4, blank beats guessed. A confidently wrong height
    pushes the right record down the ranking, while a blank one simply carries
    no weight. The forms must make "I don't know" easy, so the model has to
    permit it.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", _("Draft")
        SEARCHING = "SEARCHING", _("Searching")
        UNDER_REVIEW = "UNDER_REVIEW", _("A possible match is being reviewed")
        CONTACTED = "CONTACTED", _("You have been contacted")
        RESOLVED = "RESOLVED", _("Identified")
        WITHDRAWN = "WITHDRAWN", _("Withdrawn")

    # --- who filed it, and for which disaster -----------------------------
    # CASCADE would delete someone's report if their account went; PROTECT
    # refuses to delete the account instead. Losing a missing-person report as
    # a side effect of an account deletion is not acceptable.
    reporter = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="reports",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.PROTECT,
        related_name="reports",
        # Indexed because Phase 4 scores within one event, so every engine
        # query filters on this column.
        db_index=True,
    )

    # --- step 1 · who -----------------------------------------------------
    full_name = models.CharField(max_length=160)
    also_known_as = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Nicknames, or other spellings of the name."),
    )
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    sex = models.CharField(max_length=10, choices=Sex.choices, default=Sex.UNKNOWN)
    height_cm = models.PositiveSmallIntegerField(null=True, blank=True)
    build = models.CharField(max_length=10, choices=Build.choices, default=Build.UNKNOWN)

    # --- step 2 · where last seen -----------------------------------------
    last_seen_at = models.DateTimeField(null=True, blank=True)
    last_seen_location = models.CharField(max_length=200, blank=True)
    last_seen_region = models.ForeignKey(
        Region,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="reports_last_seen",
    )

    # --- step 3 · appearance ----------------------------------------------
    clothing_description = models.TextField(blank=True)
    distinguishing_marks = models.TextField(
        blank=True,
        help_text=_("Scars, tattoos, dental work, old injuries, anything unusual."),
    )

    # --- step 4 · contact -------------------------------------------------
    contact_phone = models.CharField(max_length=32, blank=True)
    contact_note = models.CharField(max_length=200, blank=True)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            # The family dashboard filters by reporter; the engine filters by
            # event and status. Composite indexes matching those exact queries.
            models.Index(fields=["reporter", "-created_at"]),
            models.Index(fields=["event", "status"]),
        ]

    def __str__(self):
        return f"{self.reference} · {self.full_name}"

    @property
    def reference(self):
        """The code a family quotes on the telephone.

        Derived from the primary key rather than stored. Note this is a
        DISPLAY label, not a security boundary: it is guessable, and the thing
        that stops one family reading another's report is the queryset filter
        in the view, never the unguessability of this string.
        """
        return f"KHJ-{self.pk}"

    @property
    def is_editable(self):
        """A family may edit while nobody official is acting on it.

        Once a verifier is reviewing a candidate, edits would move the ground
        under a decision in progress.
        """
        return self.status in {self.Status.DRAFT, self.Status.SEARCHING}


class ReportPhoto(models.Model):
    """A photograph supplied by the family.

    Separate model rather than an ImageField on the report, because a family
    may have several photographs and "how many" is not knowable in advance.

    upload_to keeps them under MEDIA_ROOT for now. Phase 7 moves this store
    outside the public media root entirely and serves it through a
    permission-checked view, because a guessable URL to a photograph is the
    same leak as an unscoped queryset.
    """

    report = models.ForeignKey(
        MissingPersonReport, on_delete=models.CASCADE, related_name="photos"
    )
    image = models.ImageField(upload_to="reports/%Y/%m/")
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return f"Photo for {self.report.reference}"


class UnidentifiedRecord(models.Model):
    """The responder's side: a person recovered but not yet identified.

    Deliberately parallel to MissingPersonReport, field for field, because
    the matching engine can only compare what is described in the same
    vocabulary. The asymmetry that remains is the real difficulty of the
    domain: a family knows an exact age, a mortuary knows a range; a family
    guesses a height, a mortuary measures one.
    """

    class Status(models.TextChoices):
        HELD = "HELD", _("Held, unidentified")
        UNDER_REVIEW = "UNDER_REVIEW", _("A possible match is being reviewed")
        IDENTIFIED = "IDENTIFIED", _("Identified")
        RELEASED = "RELEASED", _("Released to family")

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.PROTECT,
        related_name="records",
        db_index=True,
    )
    event = models.ForeignKey(
        Event, on_delete=models.PROTECT, related_name="records", db_index=True
    )
    filed_by = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="records_filed"
    )

    # The physical body can always be found again from the digital record.
    custody_reference = models.CharField(
        max_length=64,
        help_text=_("The reference your facility holds this person under."),
    )

    # --- estimated, not stated. This is the asymmetry with the family form.
    estimated_age_min = models.PositiveSmallIntegerField(null=True, blank=True)
    estimated_age_max = models.PositiveSmallIntegerField(null=True, blank=True)
    sex = models.CharField(max_length=10, choices=Sex.choices, default=Sex.UNKNOWN)
    height_cm = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text=_("Measured, not estimated, where possible.")
    )
    build = models.CharField(max_length=10, choices=Build.choices, default=Build.UNKNOWN)

    # --- recovery, the mirror of last-seen -------------------------------
    recovered_at = models.DateTimeField(null=True, blank=True)
    recovery_location = models.CharField(max_length=200, blank=True)
    recovery_region = models.ForeignKey(
        Region,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="records_recovered",
    )

    # --- the comparable descriptions --------------------------------------
    clothing_description = models.TextField(blank=True)
    distinguishing_marks = models.TextField(
        blank=True,
        help_text=_("Scars, tattoos, dental work, amputations, old fractures."),
    )

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.HELD)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # One custody reference per organisation. Two facilities may
            # legitimately use the same numbering, so the uniqueness is on
            # the pair, not the reference alone.
            UniqueConstraint(
                fields=["organisation", "custody_reference"],
                name="unique_custody_reference_per_organisation",
            ),
        ]
        indexes = [
            models.Index(fields=["organisation", "-created_at"]),
            models.Index(fields=["event", "status"]),
        ]

    def __str__(self):
        return self.custody_reference

    @property
    def age_range_display(self):
        low, high = self.estimated_age_min, self.estimated_age_max
        if low and high:
            return f"{low}–{high}"
        return str(low or high or "—")


class RecordPhoto(models.Model):
    """A post-mortem photograph. Restricted, and every read is logged.

    upload_to is a private prefix rather than the public media root. Phase 7
    serves these through a permission-checked view and writes an AuditEvent
    on every access — principle 5, every READ of a sensitive record is a
    logged event, not only every write.

    Until that view exists, nothing renders these to a browser.
    """

    record = models.ForeignKey(
        UnidentifiedRecord, on_delete=models.CASCADE, related_name="photos"
    )
    image = models.ImageField(upload_to="restricted/records/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return f"Restricted photo for {self.record.custody_reference}"

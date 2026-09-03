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

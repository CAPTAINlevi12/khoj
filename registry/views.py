from django.core.cache import cache
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from .models import Event, Region

RAIL_SECTIONS = [
    ("hero", _("Start")),
    ("numbers", _("Numbers")),
    ("problem", _("The problem")),
    ("how", _("How it works")),
    ("match", _("How a match is found")),
    ("helps", _("What helps")),
    ("coverage", _("Where we are connected")),
    ("privacy", _("Privacy")),
    ("offline", _("Other ways in")),
    ("questions", _("Questions")),
]


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

    Everything place-specific now comes from the database: which event the
    page describes, which districts it covers, and which facilities are
    connected. Nepal is the row that happens to be loaded, not a constant
    typed into a template.
    """
    # Each prefetch_related entry costs exactly one extra query no matter how
    # many rows come back, and it populates a cache that `.all()` reads from
    # afterwards. That matters here because several of these relations are
    # rendered twice on the page — without the cache, every `{% for %}` would
    # be another round trip. "regions__organisations" follows the relation two
    # levels deep, which is what keeps the coverage band flat.
    event = (
        Event.objects.filter(is_primary=True)
        .prefetch_related(
            "regions__organisations",
            "figures",
            "help_desks__region",
        )
        .first()
    )

    districts = event.regions.all() if event else Region.objects.none()

    return render(
        request,
        "registry/home.html",
        {
            "event": event,
            "stats": get_stats(),
            "districts": districts,
            "rail_sections": RAIL_SECTIONS,
        },
    )

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
    event = Event.objects.filter(is_primary=True).first()

    # prefetch_related pulls every region's organisations in one extra query
    # instead of one query per region — the N+1 problem, and the coverage band
    # is exactly where it would bite.
    if event:
        districts = event.regions.prefetch_related("organisations")
    else:
        districts = Region.objects.none()

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

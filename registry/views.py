from django.core.cache import cache
from django.shortcuts import render

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

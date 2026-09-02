from django.core.cache import cache
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

# Districts and facilities for the coverage band. These are hard-coded for
# now: Organisation and UnidentifiedRecord arrive in Phase 3, and this band
# reads from them once they exist.
DISTRICTS = [
    {
        "key": "rasuwa",
        "name": _("Rasuwa"),
        "path": "M30 40 L120 25 L180 55 L150 120 L60 130 Z",
        "x": 105, "y": 80,
        "facilities": [
            {"name": _("Dhunche District Hospital"), "records": 0},
            {"name": _("Rasuwa District Police Office"), "records": 0},
            {"name": _("Timure Health Post"), "records": 0},
        ],
    },
    {
        "key": "nuwakot",
        "name": _("Nuwakot"),
        "path": "M180 55 L280 40 L330 90 L250 115 Z",
        "x": 255, "y": 80,
        "facilities": [
            {"name": _("Trishuli District Hospital"), "records": 0},
            {"name": _("Betrawati Police Post"), "records": 0},
        ],
    },
    {
        "key": "chitwan",
        "name": _("Chitwan"),
        "path": "M60 130 L150 120 L170 180 L80 190 Z",
        "x": 115, "y": 160,
        "facilities": [
            {"name": _("Bharatpur Hospital"), "records": 0},
            {"name": _("Chitwan Medical College"), "records": 0},
        ],
    },
    {
        "key": "kaski",
        "name": _("Kaski"),
        "path": "M170 180 L250 115 L330 90 L340 165 L250 190 Z",
        "x": 265, "y": 155,
        "facilities": [
            {"name": _("Pokhara Academy of Health Sciences"), "records": 0},
            {"name": _("Gandaki Medical College"), "records": 0},
            {"name": _("Kaski District Police Office"), "records": 0},
        ],
    },
]

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

    Four COUNT(*) queries on every anonymous page load would be four
    queries too many on the day this page is actually busy. cache.get_or_set
    runs the callable only on a miss.

    The figures are zero until Phases 2 and 3 create the models behind
    them. Zero is the honest number; inventing traffic on a page about
    missing people would be a lie with a particularly bad shape.
    """
    return cache.get_or_set(
        "landing_stats",
        lambda: {
            "reports": 0,
            "records": 0,
            "identified": 0,
            "facilities": 0,
        },
        300,
    )


def home(request):
    """Public landing page.

    `request` is a HttpRequest object Django builds for every incoming
    request. `render` takes it, a template name, and a context dict, and
    returns a HttpResponse with the rendered HTML inside.
    """
    return render(
        request,
        "registry/home.html",
        {
            "stats": get_stats(),
            "districts": DISTRICTS,
            "rail_sections": RAIL_SECTIONS,
        },
    )

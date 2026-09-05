"""Shared reads, so two places never fetch the same row twice."""

from .models import Event

_CACHE_ATTR = "_khoj_primary_event"

# base.html cites its sources in the footer on every page, so the figures are
# always needed. Everything heavier is asked for by the view that wants it.
BASE_PREFETCH = ("figures",)


def get_primary_event(request, *prefetch):
    """Return the primary event, fetching it at most once per request.

    Both the home view and the primary_event context processor need this row.
    The cache lives on the request object because a request is a plain Python
    object — you can hang an attribute off it, and it is discarded when the
    response is sent, so nothing leaks between users.

    Ordering matters and is what makes this work: a context processor runs
    while the TEMPLATE renders, which is after the view function body. So the
    view gets there first with its heavier prefetch list, stores the result,
    and the processor finds it already cached rather than issuing a second,
    thinner query for the same row.
    """
    cached = getattr(request, _CACHE_ATTR, None)
    if cached is not None:
        return cached

    event = (
        Event.objects.filter(is_primary=True)
        .prefetch_related(*(prefetch or BASE_PREFETCH))
        .first()
    )
    setattr(request, _CACHE_ATTR, event)
    return event

from .models import Event


def primary_event(request):
    """Put the primary event into every template's context.

    A context processor is just a function taking the request and returning a
    dict, which Django merges into the context of every template rendered
    through the engine. base.html is rendered on every page, but only the home
    view puts `event` in its context — without this, the header telephone
    number would be blank everywhere else.

    The queryset is lazy: `Event.objects.filter(...).first()` runs a query per
    request, so it is cheap but not free. If the header grows more event data,
    this is the place to cache it.
    """
    return {"primary_event": Event.objects.filter(is_primary=True).first()}

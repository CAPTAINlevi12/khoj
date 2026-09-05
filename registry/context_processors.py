from .queries import get_primary_event


def primary_event(request):
    """Put the primary event into every template's context.

    A context processor is just a function taking the request and returning a
    dict, which Django merges into the context of every template rendered
    through the engine. base.html is rendered on every page, but only the home
    view puts `event` in its context — without this, the header telephone
    number and footer sources would be blank everywhere else.

    The fetch is shared with the view through get_primary_event, so a page
    that already loaded the event does not pay for it twice.
    """
    return {"primary_event": get_primary_event(request)}

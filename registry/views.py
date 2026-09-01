from django.shortcuts import render


def home(request):
    """Landing page.

    `request` is a HttpRequest object Django builds for every incoming
    request. `render` takes it, a template name, and a context dict, and
    returns a HttpResponse with the rendered HTML inside.
    """
    return render(request, "registry/home.html")

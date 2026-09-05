from django.urls import path

from . import views

urlpatterns = [
    # ""      -> matches the site root, because khoj/urls.py already ate the prefix
    # views.home -> the function object itself, NOT views.home() called
    # name=   -> the label we use in templates: {% url 'home' %}
    path("", views.home, name="home"),
    # The pages the home page hands off to. Naming them here is what lets
    # templates link with {% url 'coverage' %} instead of a literal path, so
    # a URL can be changed in one place.
    path("how-it-works/", views.how_it_works, name="how-it-works"),
    path("how-matching-works/", views.matching, name="matching"),
    path("coverage/", views.coverage, name="coverage"),
    path("privacy/", views.privacy, name="privacy"),
    path("questions/", views.questions, name="questions"),
]

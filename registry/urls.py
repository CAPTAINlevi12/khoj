from django.urls import path

from . import views

urlpatterns = [
    # ""      -> matches the site root, because khoj/urls.py already ate the prefix
    # views.home -> the function object itself, NOT views.home() called
    # name=   -> the label we use in templates: {% url 'home' %}
    path("", views.home, name="home"),
]

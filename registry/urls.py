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

    # Phase 2 · a family's own reports. Every one of these resolves through a
    # queryset filtered to request.user, so the pk in the URL is not a secret
    # and does not need to be.
    path("reports/", views.ReportListView.as_view(), name="report-list"),
    path("reports/new/", views.report_start, name="report-start"),
    path("reports/<int:pk>/", views.ReportDetailView.as_view(), name="report-detail"),
    path("reports/<int:pk>/step/<int:step>/", views.ReportStepView.as_view(), name="report-step"),
    path("reports/<int:pk>/submit/", views.ReportSubmitView.as_view(), name="report-submit"),
    path("reports/<int:pk>/photo/", views.ReportPhotoView.as_view(), name="report-photo"),
    path("reports/<int:pk>/withdraw/", views.ReportWithdrawView.as_view(), name="report-withdraw"),

    # Phase 3 · unidentified records. Scoped to the responder's own
    # organisation in the queryset, not by hiding links.
    path("records/", views.RecordListView.as_view(), name="record-list"),
    path("records/new/", views.RecordCreateView.as_view(), name="record-new"),
    path("records/<int:pk>/", views.RecordDetailView.as_view(), name="record-detail"),
]

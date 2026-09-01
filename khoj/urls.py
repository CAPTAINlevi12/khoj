from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Everything the registry app owns hangs off the site root for now.
    path("", include("registry.urls")),
]

# During development, let Django serve uploaded files.
# In production a real web server does this instead - never Django.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.contrib import admin

from .models import Event, Organisation, Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "parent")
    list_filter = ("kind",)
    search_fields = ("name",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "status", "occurred_on", "is_primary")
    list_filter = ("kind", "status", "is_primary")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("regions",)


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "region", "is_connected")
    list_filter = ("kind", "is_connected", "region")
    search_fields = ("name",)
    # A plain ForeignKey renders as a <select> holding every row. Fine at four
    # districts, unusable at four thousand, so it gets a lookup widget now.
    autocomplete_fields = ("region",)

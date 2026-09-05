from django.contrib import admin

from .models import (
    Event,
    MissingPersonReport,
    Organisation,
    RecordPhoto,
    Region,
    ReportPhoto,
    UnidentifiedRecord,
)


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


class ReportPhotoInline(admin.TabularInline):
    model = ReportPhoto
    extra = 0


@admin.register(MissingPersonReport)
class MissingPersonReportAdmin(admin.ModelAdmin):
    list_display = ("reference", "full_name", "age", "status", "event", "created_at")
    list_filter = ("status", "event", "sex")
    search_fields = ("full_name", "also_known_as", "distinguishing_marks")
    autocomplete_fields = ("last_seen_region",)
    inlines = [ReportPhotoInline]
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Reference")
    def reference(self, obj):
        return obj.reference


class RecordPhotoInline(admin.TabularInline):
    model = RecordPhoto
    extra = 0


@admin.register(UnidentifiedRecord)
class UnidentifiedRecordAdmin(admin.ModelAdmin):
    list_display = ("custody_reference", "organisation", "age_range_display", "sex", "status")
    list_filter = ("status", "organisation", "sex")
    search_fields = ("custody_reference", "distinguishing_marks")
    autocomplete_fields = ("recovery_region",)
    inlines = [RecordPhotoInline]
    readonly_fields = ("created_at", "updated_at")

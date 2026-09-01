from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Reuse Django's built-in user admin, then bolt our extra fields on."""

    list_display = ("username", "email", "role", "organisation", "is_staff")
    list_filter = BaseUserAdmin.list_filter + ("role",)

    # fieldsets controls the EDIT page. Take Django's tuple and append ours.
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Project fields", {"fields": ("role", "phone", "organisation")}),
    )

    # add_fieldsets controls the CREATE page (it is a different form).
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Project fields", {"fields": ("role", "phone", "organisation")}),
    )

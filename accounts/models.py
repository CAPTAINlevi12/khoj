from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """The project's user.

    AbstractUser already gives us username, password, email, first_name,
    last_name, is_staff, is_active, is_superuser, date_joined, last_login,
    plus the groups/permissions machinery. We inherit all of that and add
    only the fields this project needs.
    """

    class Role(models.TextChoices):
        # Left side  = what is stored in the database column
        # Middle     = the value in Python (User.Role.FAMILY == "FAMILY")
        # Right side = the human label shown in forms and the admin
        FAMILY = "FAMILY", "Family member"
        RESPONDER = "RESPONDER", "Responder (hospital / morgue / police)"
        VERIFIER = "VERIFIER", "Verifier"
        ADMIN = "ADMIN", "Administrator"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.FAMILY,
    )
    phone = models.CharField(max_length=20, blank=True)

    # Which organisation a responder belongs to (hospital, police post, NGO).
    # Blank for ordinary family accounts.
    organisation = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    # Small helpers so views and templates never compare raw strings.
    @property
    def is_responder(self):
        return self.role == self.Role.RESPONDER

    @property
    def is_verifier(self):
        return self.role == self.Role.VERIFIER

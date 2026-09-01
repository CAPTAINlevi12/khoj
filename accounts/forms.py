from django.contrib.auth.forms import UserCreationForm

from .models import User


class RegistrationForm(UserCreationForm):
    """Sign-up form for family members and the public.

    UserCreationForm already builds username + two password fields (with
    matching validation) and calls set_password() for us on save(), so a
    plaintext password never touches the database. We only add the fields
    this project needs on top.
    """

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "email", "phone"]
        # role is deliberately absent: public sign-up always creates a
        # FAMILY account (the model default). Responder/verifier accounts
        # are issued by an admin, never self-registered.

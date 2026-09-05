from django import forms
from django.utils.translation import gettext_lazy as _

from .models import MissingPersonReport, ReportPhoto, UnidentifiedRecord


class StepForm(forms.ModelForm):
    """Base for the wizard steps.

    Each step is a ModelForm over the SAME model, listing only the fields that
    step is responsible for. That is the whole trick behind the four-step
    form: `Meta.fields` decides which columns this form touches, so saving
    step 2 cannot blank out what step 1 collected — the other fields simply
    are not part of this form's cleaned_data.
    """

    class Meta:
        model = MissingPersonReport
        fields: list[str] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Nothing in this project is required except a name. Principle 4:
        # blank beats guessed, so the form must not push anyone into
        # inventing a value to get past validation.
        for name, field in self.fields.items():
            if name != "full_name":
                field.required = False


class WhoForm(StepForm):
    """Step 1 — who the person is."""

    class Meta(StepForm.Meta):
        fields = ["full_name", "also_known_as", "age", "sex", "height_cm", "build"]
        labels = {
            "full_name": _("Full name"),
            "also_known_as": _("Also known as"),
            "age": _("Age"),
            "sex": _("Sex"),
            "height_cm": _("Height in centimetres"),
            "build": _("Build"),
        }
        help_texts = {
            "age": _("Roughly is fine. Leave blank if you are not sure."),
            "height_cm": _("An estimate is fine. Leave blank if you are not sure."),
        }


class WhereForm(StepForm):
    """Step 2 — where and when they were last seen."""

    class Meta(StepForm.Meta):
        fields = ["last_seen_at", "last_seen_location", "last_seen_region"]
        labels = {
            "last_seen_at": _("When were they last seen?"),
            "last_seen_location": _("Where were they last seen?"),
            "last_seen_region": _("District"),
        }
        help_texts = {
            "last_seen_at": _("The date, and roughly what time if you remember."),
            "last_seen_location": _("A place name is enough — a village, a bridge, a road."),
        }
        widgets = {
            # type="datetime-local" gives a native picker on a phone, which
            # matters more than it sounds when the person filling this in is
            # distressed and using a borrowed handset.
            "last_seen_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only offer districts that belong to this event. A queryset on the
        # field is also a validation rule: Django re-checks the submitted id
        # against it, so a hand-edited form cannot attach a region from
        # another country's disaster.
        instance = kwargs.get("instance") or self.instance
        if instance and instance.event_id:
            self.fields["last_seen_region"].queryset = instance.event.regions.all()


class AppearanceForm(StepForm):
    """Step 3 — the section that matters most to the matching engine."""

    class Meta(StepForm.Meta):
        fields = ["clothing_description", "distinguishing_marks"]
        labels = {
            "clothing_description": _("What were they wearing when last seen?"),
            "distinguishing_marks": _("Scars, tattoos, dental work, old injuries"),
        }
        help_texts = {
            "distinguishing_marks": _(
                "This section matters most. Details like these identify people "
                "when nothing else can. Write everything you remember, even if "
                "it feels small."
            ),
        }
        widgets = {
            "clothing_description": forms.Textarea(attrs={"rows": 3}),
            "distinguishing_marks": forms.Textarea(attrs={"rows": 4}),
        }


class ContactForm(StepForm):
    """Step 4 — how an official reaches a person who will answer."""

    class Meta(StepForm.Meta):
        fields = ["contact_phone", "contact_note"]
        labels = {
            "contact_phone": _("Telephone number"),
            "contact_note": _("Anything else we should know when we call"),
        }
        help_texts = {
            "contact_phone": _(
                "Give a number someone will answer. It may be yours, a "
                "neighbour's, or a relative's."
            ),
        }


class PhotoForm(forms.ModelForm):
    """One photograph at a time, added from the appearance step."""

    class Meta:
        model = ReportPhoto
        fields = ["image", "caption"]
        labels = {
            "image": _("Photograph"),
            "caption": _("When was it taken?"),
        }


class UnidentifiedRecordForm(forms.ModelForm):
    """Responder intake.

    One screen, not a wizard: these arrive in batches and the person filling
    it in is working at speed under load. The family form is four short steps
    because it is filled once, in distress; this one is optimised for the
    opposite situation.

    Same field vocabulary as the family form, deliberately, so the two sides
    are genuinely comparable.
    """

    class Meta:
        model = UnidentifiedRecord
        fields = [
            "custody_reference",
            "recovered_at",
            "recovery_location",
            "recovery_region",
            "estimated_age_min",
            "estimated_age_max",
            "sex",
            "height_cm",
            "build",
            "clothing_description",
            "distinguishing_marks",
        ]
        labels = {
            "custody_reference": _("Custody reference"),
            "recovered_at": _("Recovered at"),
            "recovery_location": _("Recovery location"),
            "recovery_region": _("District"),
            "estimated_age_min": _("Estimated age from"),
            "estimated_age_max": _("Estimated age to"),
            "sex": _("Sex"),
            "height_cm": _("Height in centimetres"),
            "build": _("Build"),
            "clothing_description": _("Clothing recovered with"),
            "distinguishing_marks": _("Distinguishing features"),
        }
        widgets = {
            "recovered_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "clothing_description": forms.Textarea(attrs={"rows": 3}),
            "distinguishing_marks": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != "custody_reference":
                field.required = False
        if event is not None:
            # Same trick as the family form: a field queryset is also a
            # validation rule, so a hand-edited POST cannot attach a region
            # belonging to another event.
            self.fields["recovery_region"].queryset = event.regions.all()

    def clean(self):
        cleaned = super().clean()
        low = cleaned.get("estimated_age_min")
        high = cleaned.get("estimated_age_max")
        if low and high and low > high:
            # A reversed range would silently never match anyone, because the
            # engine asks whether a stated age falls inside the band.
            raise forms.ValidationError(
                _("The age range is the wrong way round — 'from' must be lower than 'to'.")
            )
        return cleaned

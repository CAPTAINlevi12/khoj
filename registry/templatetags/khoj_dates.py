"""Date formatting that respects the deployment's calendar.

A template tag library is any module inside a `templatetags` package in an
installed app. Django imports it when a template says {% load khoj_dates %},
and every function decorated with @register.simple_tag becomes a tag.
"""

from django import template
from django.utils import timezone
from django.utils.translation import gettext as _

register = template.Library()

# nepali_datetime is optional. Guarding the import means a deployment that
# does not need Bikram Sambat — every non-Nepali one — does not have to carry
# the dependency, and the site degrades to Gregorian rather than crashing.
try:
    import nepali_datetime
except ImportError:  # pragma: no cover
    nepali_datetime = None


def _bikram_sambat(value):
    """Convert a date to Bikram Sambat, or return None if we cannot.

    Deliberately no fallback arithmetic. Bikram Sambat month lengths vary
    year to year and are not derivable from a formula — they come from a
    lookup table — so a hand-rolled approximation produces dates that are
    quietly wrong. Better to show one correct calendar than two where one is
    invented.
    """
    if nepali_datetime is None:
        return None
    try:
        bs = nepali_datetime.date.from_datetime_date(value)
        return bs.strftime("%d %B %Y")
    except Exception:
        # Out of the library's supported range, most likely.
        return None


@register.simple_tag
def stamp(value, calendar=None, with_time=True):
    """Render a timestamp, optionally alongside a second calendar.

    Usage:  {% stamp event.data_updated_at event.secondary_calendar %}
    """
    if not value:
        return _("not recorded")

    # USE_TZ is on, so values come out of the database in UTC. localtime()
    # converts to TIME_ZONE before anything is formatted — otherwise the date
    # itself can be wrong by a day near midnight, which then converts to the
    # wrong Bikram Sambat day too.
    if timezone.is_aware(value):
        value = timezone.localtime(value)

    gregorian = value.strftime("%d %b %Y, %H:%M" if with_time else "%d %b %Y")

    if calendar == "BIKRAM_SAMBAT":
        secondary = _bikram_sambat(value.date())
        if secondary:
            return f"{secondary} · {gregorian}"

    return gregorian

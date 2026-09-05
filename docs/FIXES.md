# Fix list — review of the generic-registry work

Reviewed at commit `91d731d`. Three defects, one coupling risk, one question
for Abhinav. Ordered by priority. Each one says *why* it matters, not just
what to change.

The generalisation itself is good and none of this touches it. `Region` as a
self-referencing tree, `Event.geography_rule` turning `kind` into a behaviour
switch rather than a label, `EventFigure` carrying its `source`, and the
partial unique index on `is_primary` are all right. Leave them alone.

---

## 1 — The "last updated" stamp is hardcoded and lies · HIGH

**Where**
- `templates/base.html:143`
- `registry/templates/registry/_band_counters.html:30`

Both contain the literal string `29 Bhadra 2083 · 29 Aug 2026, 14:20`.

**Why it matters.** The comment directly above it in `_band_counters.html`
says it: *"An emergency page has to timestamp itself: a visitor has no other
way to tell a live service from an abandoned one."* A stamp that always reads
29 August does the opposite of its job — it is worse than having no stamp,
because it actively asserts something false. It also survived a commit whose
message says the last Nepal strings were removed: Bikram Sambat is the Nepali
calendar, so this is both a lie and a leftover hardcode.

**Fix**

1. Add to `Event`:

   ```python
   updated_at = models.DateTimeField(auto_now=True)
   ```

   `auto_now=True` writes the current time on every save. Note what that
   honestly means: *when this event's data last changed*, not when a report
   arrived. That is the correct claim for this page today. When Phase 2 adds
   reports, revisit it so it reflects the newest record instead.

2. Render it from data in both templates:

   ```django
   {% translate "Last updated" %}
   <time datetime="{{ primary_event.updated_at|date:'c' }}" class="mono">
     {{ primary_event.updated_at|date:"j M Y, H:i" }}
   </time>
   ```

   `primary_event` is already in every template via the context processor, so
   `base.html` needs nothing new. Use a real `<time datetime="...">` element —
   the machine-readable attribute is what makes the date meaningful to
   screen readers and crawlers, and `|date:'c'` emits ISO 8601.

3. **Drop the Bikram Sambat half for now.** Converting Gregorian to BS is a
   lookup table, not arithmetic — month lengths vary year to year and cannot
   be computed. Faking it would produce wrong dates on a page whose whole
   argument is that it does not print numbers it cannot stand behind.

   When you do want it, add a real dependency (`nepali-datetime`) and put the
   calendar on the event so it stays per-deployment:

   ```python
   class Calendar(models.TextChoices):
       GREGORIAN = "GREGORIAN", _("Gregorian")
       BIKRAM_SAMBAT = "BIKRAM_SAMBAT", _("Bikram Sambat")
   ```

   Then a template filter renders the second date only when the event asks
   for it. A Türkiye deployment would never show BS.

---

## 2 — CRLF line endings are poisoning every diff · HIGH

**Where**
- `registry/migrations/0001_initial.py`
- `registry/migrations/0002_event_hotline_*.py`
- `templates/base.html`

**Why it matters.** `git diff` reports 264 changed lines across these files
while `git diff --ignore-cr-at-eol` reports nothing at all — the content is
identical and only the line endings differ. There is no `.gitattributes`, so
Windows tooling keeps writing CRLF and Git keeps seeing whole-file rewrites.
Left alone, every future diff on these files is unreviewable: a genuine
one-line change is buried in hundreds of fake ones, and that is exactly how a
real bug slips through review unnoticed.

**Fix**

1. Create `.gitattributes` at the repo root:

   ```
   * text=auto eol=lf
   *.png binary
   *.jpg binary
   *.pdf binary
   ```

   `text=auto` lets Git decide what is text; `eol=lf` normalises it in the
   repository. Working files on Windows are unaffected.

2. Normalise what is already committed:

   ```
   git add --renormalize .
   git commit -m "chore: normalise line endings to LF"
   ```

3. Confirm `git diff` is empty afterwards.

Do this as its own commit with nothing else in it, so the one noisy diff in
the project's history is clearly labelled.

---

## 3 — The primary event is fetched twice per page load · LOW

**Where**
- `registry/views.py` — `Event.objects.filter(is_primary=True)...first()`
- `registry/context_processors.py` — the same query again

**Why it matters.** The context processor runs for every template rendered
through the engine, and `home()` already fetched the event with its
prefetches. On the home page that is two queries where one would do, and the
context processor's copy has no prefetch — so anything in `base.html` that
touches a relation would trigger further queries.

Small today. Worth fixing now because it is three lines, and because the
pattern (view and context processor silently duplicating work) gets copied
into every later page.

**Fix.** Cache it in the context processor, keyed and short-lived, the same
way `get_stats()` already does:

```python
from django.core.cache import cache

def primary_event(request):
    return {
        "primary_event": cache.get_or_set(
            "primary_event",
            lambda: Event.objects.filter(is_primary=True).first(),
            300,
        )
    }
```

Caching a model instance is fine here — it is small and read-only on this
path. Invalidate on `Event` save later if it becomes stale-sensitive.

---

## 4 — `RAIL_SECTIONS` and the band includes can drift apart · COUPLING RISK

**Where**
- `registry/views.py` — the `RAIL_SECTIONS` list
- `registry/templates/registry/home.html` — the `{% include %}` list

Two hand-maintained lists describing the same page. Remove a band from the
template and the scroll rail still advertises it, producing a nav link to an
anchor that no longer exists. Nothing is broken today; the two lists agree.

**Fix (only when the bands change).** Make one list the source of truth —
each entry carries its anchor, its label and its template path, and
`home.html` loops over it. Not worth doing until the band set actually
changes, which is what question 5 decides.

---

## 5 — The home page is back to ten bands · QUESTION, NOT A DEFECT

`home.html` includes: event, hero, counters, problem, how, match, signals,
coverage, trust, offline, questions.

Abhinav asked for a slim home page that hands off to detail pages, and the
six-screen mockup did exactly that. The built page is the dense version
again. That may be deliberate — but it drifted rather than being decided, so
it should be settled explicitly before more is built on top of it.

**Do not change this without asking him.** If he wants it slim, the earlier
plan stands: keep hero, counters and the offline routes on home; move how,
match, signals, coverage, trust and questions to their own pages behind link
cards. Then fix `RAIL_SECTIONS` per item 4.

---

## Also noticed, no action needed

- `.claude/settings.json` is untracked. Decide whether it is shared config
  (commit it) or local preference (add to `.gitignore`). Either is fine; the
  current state means it silently follows nobody.
- `Organisation.record_count` returns a hardcoded `0`. Correct and honestly
  documented until Phase 3 creates `UnidentifiedRecord`. Leave it.
- The word "Nepal" remains in docstrings and comments in `models.py`,
  `views.py`, `settings.py` and `_band_event.html`. Those are explanations of
  why the design is shaped as it is, not hardcoded behaviour. Keep them —
  they are the reason the abstraction is understandable.

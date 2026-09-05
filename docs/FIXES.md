# Fix list — review of the generic-registry work

Reviewed at `91d731d`, revised at `1e0b2a2`. One defect outstanding, one
coupling risk, one question for Abhinav.

The generalisation itself is good and none of this touches it. `Region` as a
self-referencing tree, `Event.geography_rule` turning `kind` into a behaviour
switch rather than a label, `EventFigure` carrying its `source`, and the
partial unique index on `is_primary` are all right. Leave them alone.

---

## Already fixed — the hardcoded "last updated" stamp

Landed in `1e0b2a2` before this list was written. `Event.updated_at`, a
`data_updated_at` property, a `secondary_calendar` field and a `{% stamp %}`
template tag; no `Bhadra` string survives anywhere in the code.

Solved better than it was going to be specified. Putting the calendar on the
event is the right call — it keeps Bikram Sambat as a per-deployment choice
rather than a global assumption, so a Türkiye deployment shows Gregorian only.
No further action.

---

## 1 — CRLF line endings are poisoning every diff · HIGH

**Where** — `registry/migrations/0001_initial.py`,
`registry/migrations/0002_event_hotline_*.py`, `templates/base.html`,
`requirements.txt`, and spreading.

**Why it matters.** `git diff` reports ~296 changed lines across these files
while `git diff --ignore-cr-at-eol` reports nothing at all — the content is
identical and only the line endings differ. There is no `.gitattributes`, so
Windows tooling keeps writing CRLF and Git keeps seeing whole-file rewrites.

Left alone, every future diff on these files is unreviewable: a genuine
one-line change sits buried in hundreds of fake ones. That is precisely how a
real bug survives review. The file list is growing — `requirements.txt` was
not affected at the last review and is now.

**Fix**

1. Create `.gitattributes` at the repo root:

   ```
   * text=auto eol=lf
   *.png binary
   *.jpg binary
   *.pdf binary
   ```

   `text=auto` lets Git decide what counts as text; `eol=lf` normalises it
   inside the repository. Working files on Windows are unaffected — this is a
   storage-format setting, not an editor setting.

2. Normalise what is already committed:

   ```
   git add --renormalize .
   git commit -m "chore: normalise line endings to LF"
   ```

3. Confirm `git diff` comes back empty afterwards.

Do this as its own commit containing nothing else, so the one unavoidably
noisy diff in the project's history is clearly labelled as such.

---

## 2 — The primary event is fetched twice per page load · LOW

**Where** — `registry/views.py` (`Event.objects.filter(is_primary=True)...`)
and `registry/context_processors.py`, which runs the same query again.

**Why it matters.** The context processor runs for every template rendered
through the engine, and `home()` has already fetched the event *with* its
prefetches. On the home page that is two queries where one would do — and the
context processor's copy carries no prefetch, so anything in `base.html` that
reaches into a relation triggers further queries.

Small today. Worth fixing now because it is three lines, and because the
pattern — a view and a context processor silently duplicating work — is the
kind of thing that gets copied into every later page.

**Fix.** Cache it, short-lived, exactly as `get_stats()` already does:

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

Caching a model instance is fine on this path — small, read-only. If it later
becomes stale-sensitive, invalidate on `Event` save.

Note this interacts with the stamp fix: a cached event means `data_updated_at`
can lag by up to five minutes. That is acceptable for a page-level stamp, but
it is a real trade and should be a deliberate one.

---

## 3 — `RAIL_SECTIONS` and the band includes can drift apart · COUPLING RISK

**Where** — the `RAIL_SECTIONS` list in `registry/views.py`, and the
`{% include %}` list in `registry/templates/registry/home.html`.

Two hand-maintained lists describing the same page. Remove a band from the
template and the scroll rail still advertises it, producing a nav link to an
anchor that no longer exists. Nothing is broken today; the two lists agree.

**Fix (only when the bands change).** Make one list the source of truth — each
entry carrying its anchor, its label and its template path — and have
`home.html` loop over it. Not worth doing until the band set actually changes,
which is what question 4 decides.

---

## 4 — The home page is back to ten bands · QUESTION, NOT A DEFECT

`home.html` includes: event, hero, counters, problem, how, match, signals,
coverage, trust, offline, questions.

Abhinav asked for a slim home page that hands off to detail pages, and the
six-screen mockup did exactly that. The built page is the dense version again.
That may well be deliberate — but it drifted rather than being decided, and it
should be settled explicitly before more is built on top of it.

**Do not change this without asking him.** If he wants it slim, the earlier
plan stands: keep hero, counters and the offline routes on home; move how,
match, signals, coverage, trust and questions onto their own pages behind link
cards. Then fix `RAIL_SECTIONS` per item 3.

---

## Also noticed, no action needed

- `.claude/settings.json` is untracked. Decide whether it is shared config
  (commit it) or local preference (add to `.gitignore`). Either is fine; the
  current state means it silently follows nobody.
- `Organisation.record_count` returns a hardcoded `0`. Correct and honestly
  documented until Phase 3 creates `UnidentifiedRecord`. Leave it.
- The word "Nepal" remains in docstrings and comments across `models.py`,
  `views.py`, `settings.py` and `_band_event.html`. Those explain *why* the
  design is shaped as it is; they are not hardcoded behaviour. Keep them —
  they are what makes the abstraction understandable to the next reader.

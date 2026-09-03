# Khoj — project context

Read this before doing anything. It carries the decisions already made so they
don't get re-litigated or accidentally reversed.

Full design spec with wireframes: `docs/Khoj-Design-and-Roadmap.pdf`.

---

## What this is

A disaster missing-persons registry and remains-matching system, in Django.

Two populations of records are created independently by people who never meet,
and the system brings them together:

- A **family** files a missing-person report (name, age, last-seen location,
  clothing, distinguishing marks, photo).
- A **responder** (hospital / morgue / police post) files an unidentified-remains
  record (recovery location, estimated age, height, clothing, features, photo).
- A **matching engine** scores every pair and surfaces ranked candidates.
- A **verifier** — a human — confirms or rejects. The family is then contacted
  by a person.

### Why it exists

Modelled on the 26 August 2026 Langtang-Lirung glacier collapse and Bhotekoshi
flood (Rasuwa and Nuwakot districts, ~800 dead, ~3,000 missing). No central
registry existed. Families travelled hundreds of kilometres between hospitals,
morgues, police stations and army camps across six districts, filing past
photographs of unidentified bodies. Families without money or internet access
could not search at all.

The system exists so that the search costs a form, not a bus fare across six
districts.

## Ground rule — do not deploy this

**This is a learning and portfolio project running on seeded, fictional data.**
It is not deployed as a public service and must not accept real reports.

A student-built site that looks like an official registry during a live disaster
splinters the search into one more place to check, collects the personal data of
people at their most vulnerable, and attracts donation fraud impersonating it.

Keep the "not an official registry" disclaimer in the base template footer.
Never wire in real victim data or donation flows. If a relief organisation ever
wants this, that is a conversation with them — not a solo launch.

---

## How Abhinav wants to be taught

He is a 3rd-year CSE student aiming at secure backend / AppSec work. He is
building this to **learn Django**, not to get a finished app handed over.

- Write the code **and explain the Django machinery behind it** — in the same
  turn, not afterwards.
- Explanations are **object-oriented and foundational**: what the object is,
  what the dot means, what belongs to the object, how `self` and methods work.
- Explain **why the syntax works**, never "just write this". Connect Django
  behaviour back to plain Python — a `Meta` class is a nested class, a mixin is
  multiple inheritance, `@property` is a descriptor.
- Give **the next useful step**, not a twenty-item list.
- Simple analogies, direct corrections, plain language.
- He pushes back when reasoning is inconsistent. That is welcome — engage with
  it rather than folding.

Note: on his previous project he wrote all the logic himself and asked for help
when stuck. **He deliberately flipped that for this project** — here he wants the
code written and taught, and he names the features to add. Do not hand logic
back to him as an exercise unless he asks.

---

## Environment

- Windows, VS Code, project at `D:\Djangoprojects\project#2`.
- **C: is full. Never write to C:.** Use `pip install --no-cache-dir` so pip's
  wheel cache does not land in `C:\Users\...\AppData\Local\pip\Cache`.
- Windows venv at `.\venv` (gitignored). Activate with `venv\Scripts\activate`.
- GitHub: `CAPTAINlevi12/khoj`, public.

## Stack and decisions made

| Decision | Why |
|---|---|
| Custom user model from the first migration | `AUTH_USER_MODEL = "accounts.User"`, subclassing `AbstractUser` with `role` / `phone` / `organisation`. Set before the first `migrate` so auth and admin FKs point at the right table. Changing it later is a rewrite. |
| PostgreSQL from the start (moved up from Phase 8) | Originally planned as SQLite-until-Phase-8, but Abhinav already had Postgres 18 installed locally (`D:\postgre`), so switched immediately rather than migrating later. Trigram similarity for Nepali name variants (Shrestha / Shreshtha / Sreshtha) still lands in Phase 8 — that phase is now "add trigram search" only, not "migrate database". |
| Django 6.1, not 5.1.5 as originally pinned | Global Python is 3.14.6, which Django 5.1 does not officially support. Bumped to 6.1 rather than pin an unsupported combination. |
| Secrets via `.env` + `python-dotenv` + `os.getenv()` | `.env` is gitignored; `.env.example` is committed. Never commit `.env`. |
| Bootstrap 5 via CDN | Not a frontend project. Structure over skin. |
| Project-wide `templates/` plus per-app template dirs | `DIRS` for shared, `APP_DIRS` for app-local. |
| `Event` / `Region` models — Nepal is data, not code | Khoj is a registry for sudden-onset disasters that currently has **one event loaded**, not a Nepal-specific site. Districts and facilities are rows; the landing page reads the primary event from the database. Deploying for an earthquake elsewhere is a new row. Done before Phase 2 so `MissingPersonReport` is born with the FK instead of being retrofitted. |
| `Organisation` model pulled forward from Phase 3 | The coverage band cannot stop hardcoding facility names without it. Only the *model* moved; Phase 3 still owns responder intake and org-scoped querysets. |

Apps: `accounts` (custom User), `registry` (reports, records, matches).

---

## Domain design principles — do not quietly violate these

1. **The machine proposes, a person decides.** No automatic confirmation at any
   score. 99 is still a candidate.
2. **Families never browse the dead.** No public gallery, no family-facing search
   over remains. A family sees a photograph only when a verifier deliberately
   shows them one. Do not add a "search all records" feature for families,
   however obvious it seems.
3. **Show the reasoning, not just the score.** The verifier sees the per-signal
   breakdown, never a bare number. A decision this serious must be interrogable.
4. **Blank beats guessed.** Forms should make "I don't know" easy. A confident
   wrong height buries the right match.
5. **Every *read* of a sensitive record is logged**, not only every write.
6. **Honest status, never false comfort.** "Searching" is true; "No match found"
   is a verdict the system has not earned.
7. **Ownership is enforced in the queryset, not the template.** Hiding a link is
   not access control. IDOR — changing the id in a URL — is the bug class to
   design against.

## Matching engine (Phase 4)

A transparent scoring function, not ML — every point must be explainable aloud.
Max 100:

| Signal | Points | Note |
|---|---|---|
| Distinguishing marks | 25 | Scars, tattoos, dental work. Near-unique. |
| Clothing | 20 | Token overlap, colour-normalised. |
| Age | 18 | Stated age against estimated band. |
| Geography and time | 15 | **The rule depends on `Event.kind`** — see `Event.geography_rule`. For a flood or glacier collapse it is `downstream`: recovery point must be downstream of last-seen within a plausible drift interval, and upstream scores zero, because water goes one way. For an earthquake or fire nothing drifts, so it is `proximity`. For a landslide, `downslope`. |
| Height | 12 | ±4 cm full, decaying to zero at ±15 cm. |
| Sex and build | 10 | Soft — post-mortem estimates get revised. |

Thresholds: <30 discarded (no row written), 30–55 weak candidate, >55 surfaced.
Any marks hit above 15 is always surfaced regardless of total.

Match states: `SUGGESTED` → `UNDER_REVIEW` → `FAMILY_CONTACTED` → `CONFIRMED`,
with `REJECTED` (reason mandatory) and `SUPERSEDED` (auto, when the other side is
confirmed elsewhere). Confirmation runs inside `transaction.atomic`.

---

## Roadmap

Detail, wireframes and the "done when" test for each phase are in
`docs/Khoj-Design-and-Roadmap.pdf`.

- **Phase 0 — Foundation.** DONE. Scaffold, custom user, env secrets, base template.
- **Phase 1 — Accounts and role gates.** NEXT. Registration, login/logout,
  role-routed dashboards, a reusable mixin that 403s the wrong role.
  *Done when:* a family account signing in lands on the family dashboard and a
  hand-typed `/verifier/queue/` returns 403.
- **Phase 2 — Missing-person reports.** Model, four-step wizard, photo upload,
  own-reports list, status timeline. *Done when:* a family cannot open another
  family's report by changing the id in the URL.
- **Phase 3 — Unidentified records.** `UnidentifiedRecord`, responder intake,
  org-scoped querysets. (`Organisation` already exists — built early, see the
  decisions table.) *Done when:* two responders in different organisations see
  disjoint lists, proven by a test.
- **Phase 4 — Matching engine.** `MatchCandidate` as a `through` model, pure-Python
  scoring module (no Django imports, so it is unit-testable), management command.
  **Scoring is scoped to one `Event`** — a Nepal report must never be compared
  against Turkish remains, and partitioning by event is also what keeps the
  O(reports × records) comparison tractable. The geography signal picks its
  strategy from `Event.geography_rule`.
- **Phase 5 — Verifier queue and comparison.** Ranked queue, side-by-side screen,
  computed agreements/disagreements, atomic state transitions, `select_for_update`.
- **Phase 6 — Notifications.** Email/SMS on state change, queued and idempotent.
- **Phase 7 — Security hardening.** Private media behind a permission-checked
  view, append-only audit log, rate limiting, `check --deploy` clean.
- **Phase 8 — PostgreSQL and real search.** Trigram similarity, full-text, GIN indexes.
- **Phase 9 — API and public statistics.** DRF read-only API, aggregate dashboard.
- **Phase 10 — Seed data, tests, deployment.** Fixture generator with *planted*
  matches (that is how the engine is proven), permission-matrix tests, Docker.

---

## Conventions

**Commits.** One per working thing, not one per day. The test is: *could this be
checked out fresh and would it run?* If yes, commit; broken half-states stay
uncommitted. Conventional style — `feat:`, `fix:`, `chore:`, `test:` — with a
body explaining *why*, not what.

**Never commit:** `.env`, `db.sqlite3`, `venv/`, `media/`. Already in `.gitignore`
— check `git status` before committing anyway. A leaked `SECRET_KEY` is the one
Django mistake that is genuinely hard to undo, because deleting the file later
does not remove it from history.

**Multiple Claude sessions.** Abhinav sometimes has another Claude session working
on this same folder (a cloud session with web search and document generation; it
handles research, specs and design, and cannot run Windows commands). Same disk,
no locking. **Only one writes at a time** or edits get clobbered mid-change.

## Positioning — how to describe this

It is **a missing-persons registry for disaster response**, seeded with the
August 2026 Bhotekoshi flood as its worked example. Not "a Nepal flood site".

The specificity is the evidence, not a limitation: the Nepal failure is
documented in detail — families driving between six districts, no central
registry, about a thousand people a day filing past photographs in Pokhara —
which is why particular screens refuse particular features. Point at the
reporting to explain why there is no photo gallery.

Note also that identification work runs for **months to years** after recovery
ends. What finishes early is the news coverage, not the problem.

## Current state

Phase 0 complete and verified:

- Dependencies installed, `manage.py check` clean.
- `accounts.0001_initial` applied before `admin.0001_initial` — confirmed.
- `db.sqlite3` built. Superuser `abhinav` exists (dev password was shared in
  chat and should be changed).
- Verified by driving the app, not just by absence of crashes: `GET /` → 200
  through `registry/home.html` → `base.html`; `/admin/` → 302 to login when
  anonymous; admin user change form exposes `role`, `phone`, `organisation`.
- Two commits on `main`.

# Build brief — Khoj public landing page

**For whoever implements this.** Read `CLAUDE.md` first; it holds the ground rules
this brief assumes. Build exactly what is specified here, then stop and show it.

---

## 1. What this page is for

The visitor is someone who has just learned a person they love is missing, or a
relative helping them, arriving from a Facebook post or a phone recommendation.
They have never seen this site. They are deciding, in about eight seconds,
whether it can help them.

The page has to answer three questions in that time:

1. What is this?
2. Can it help me find my person?
3. What do I do right now?

Everything else on the page is secondary to those three.

### Two design decisions taken before you start

**This page is engaging, not flashy.** Rich content, real interaction, a page
worth scrolling — but the register is a public-service instrument, not a startup
launch. The reason is not taste. It is that a bereaved person reading breezy
marketing copy about their missing father closes the tab, and a 4 MB hero video
never loads at all on a 2G connection in Rasuwa. Craft here means clarity,
speed and calm, and that is a higher bar than decoration, not a lower one.

**Design for the connection, not the office.** Google Person Finder's 2010
Pakistan deployment is generally judged a failure for one reason: the people who
needed it had no internet access. Assume a five-year-old Android phone on a
congested mobile network. Every choice below follows from that.

---

## 2. Non-negotiables

- **No public search over records.** No gallery of the recovered, no browsing,
  no names, no photographs of remains anywhere on this page. Counts only.
  See principle 2 in `CLAUDE.md` — this will feel like an obvious missing
  feature. It is not missing. It is refused.
- **The "not an official registry, seeded data" disclaimer stays in the footer.**
- **No donation button, no payment flow, nothing that solicits money.**
- **Page must be usable with images off and JavaScript off.** JS enhances; it
  never gates content.
- **Every section visible at rest.** No scroll-triggered fade-ins parked at
  `opacity: 0`. On a slow connection a reveal that never fires is a blank page.

---

## 3. Page structure

Ten bands, top to bottom. Build them in this order.

### Band 1 — Header

Slim. Logo `Khoj` with `खोज` beside it. Then, right-aligned:

- **Language toggle: नेपाली / English.** Not optional. A Nepali family is the
  primary user; an English-only page fails them. Wire it with Django's `i18n`
  (`{% trans %}`, `LocaleMiddleware`, `set_language` view) even if the Nepali
  strings start as `TODO`. Retrofitting i18n later is far more work.
- **A telephone number as a `tel:` link.** Some visitors cannot use a web form
  at all. The phone number is a first-class element of this page, not a footer
  afterthought.
- **Sign in** (text link, quiet — most visitors are not returning users).

On scroll past the hero, the header becomes sticky and gains the two primary
action buttons in compact form. `position: sticky`, CSS only.

### Band 2 — Hero

The most important band. Keep it to what fits one phone screen.

- Headline: **Search for a missing person in one place.**
- Sub: *File one report. Every connected hospital, morgue and police post is
  searched for you, and an official will contact you directly.*
- Then, immediately, **the two-button split.** This pattern is the established
  convention for this class of system — Google Person Finder has used the same
  two doors since 2010, because every visitor is one of exactly two people:

  | Button | Goes to | Sub-label |
  |---|---|---|
  | **Someone I know is missing** | family registration → report wizard | I want to file a report |
  | **I have information about someone** | responder sign-in / access request | I work at a hospital, morgue or police post |

  Make them large, side by side on desktop, stacked full-width on mobile. These
  are the two biggest tap targets on the page by a wide margin.

- Under the buttons, in plain text: **You do not need to travel.**

  This is the single most important sentence on the site. It is what the page is
  *for* — someone is deciding right now whether to get on a bus to Pokhara.
  Do not bury it, do not shrink it, do not make it a footnote.

**No hero image, no video, no carousel, no parallax.** Type and buttons only.

### Band 3 — Counters

Four figures: reports filed, records held, people identified, facilities
connected. Real numbers from the database (`Model.objects.count()`), cached.

- `font-variant-numeric: tabular-nums`.
- **No count-up animation.** It trivialises what the numbers are.
- Under them: **Last updated 29 Bhadra 2083 · 29 Aug 2026, 14:20.** Emergency
  pages must timestamp themselves; a visitor has no other way to know whether
  they are looking at something live or something abandoned.

### Band 4 — How it works

Three steps, showing the two-sided flow meeting in the middle:

1. **You describe them.** What they were wearing, any scars or tattoos, where
   they were last seen.
2. **Facilities describe who they have received.** Hospitals, morgues and police
   posts record the same details for people who have not been identified.
3. **An official compares the two and contacts you.** Every possible match is
   checked by a trained person before anyone is told anything.

Illustrate with **inline SVG** — two columns of small shapes converging on a
single point. Hand-drawn SVG, not an image file: it is a few hundred bytes,
scales, and works with images disabled. Give it `role="img"` and a `<title>`.

Step 3 is doing quiet, important work: it tells the visitor a human is involved.
That is what makes the site trustworthy rather than sinister.

### Band 5 — What helps us find someone

Teaches the visitor what to remember *before* they open the form. This is a real
feature, not filler — it measurably improves the quality of what gets filed.

Four cards, ordered by how much they actually help:

- **Scars, tattoos, dental work** — the most identifying thing there is. An old
  fracture or a missing tooth can identify someone when nothing else can.
- **What they were wearing** — colours and patterns, described the way you
  remember them.
- **Where and when you last saw them** — a place name and roughly what time.
- **A clear photograph** — face visible, any age.

Then, prominently: **If you are not sure about something, leave it blank.
A guess is worse than a gap.**

### Band 6 — Where we are connected

Answers "is the hospital my brother might be in part of this?"

- A **static SVG map** of the affected districts with connected facilities
  marked. **Not** Leaflet, not Google Maps, not a tile layer. Cell service is
  unreliable in exactly the places this matters, and a map that needs to fetch
  tiles is a map that does not load. A static SVG also prints.
- Beside it, a plain list of connected facilities grouped by district: Rasuwa,
  Nuwakot, Chitwan, Nawalpur, Tanahun, Kaski.
- A line for facilities not yet connected, with a contact route.

### Band 7 — What happens to what you tell us

Trust band. Four short commitments, plainly worded:

- Your report is visible to you and to the officials reviewing possible matches.
  Nobody else.
- Photographs are never shown publicly and never shown to other families.
- Every time an official opens a record, it is recorded — who, and when.
- You can withdraw your report at any time.

Do not decorate this with lock icons and shields. Plain sentences carry more
weight here than security iconography, which reads as marketing.

### Band 8 — If you cannot use this website

Directly addresses the population Person Finder lost in 2010.

- **Telephone** — the number again, large, as a `tel:` link, with hours.
- **In person** — help desks, with locations.
- **Someone can file on your behalf** — a relative, a neighbour, a volunteer.
  Explain that this is allowed and normal.

### Band 9 — Questions

Accordion, built with `<details>` / `<summary>` — native HTML, works without
JavaScript, accessible for free. Do not hand-roll this in JS.

Ask the questions people actually have, including the uncomfortable ones:

- Will you show me photographs of bodies?
- What happens if the match is wrong?
- How long does this take?
- Is this the government?
- What if I do not know my relative's exact age or height?
- Can I file a report for a neighbour?
- What happens after someone is identified?

Answer plainly. Never promise an outcome. "Searching" is honest; "we will find
them" is not.

### Band 10 — Footer

Contact, language toggle again, the disclaimer, last-updated timestamp.

---

## 4. Trauma-informed content rules

These govern every word on the page. They come from established trauma-informed
content design practice and they are not stylistic preferences.

- **No urgency pressure.** No countdowns, no "act now", no red banners. The
  visitor is already under more pressure than any interface can add.
- **No blame in any error message.** "That date doesn't look right — it should
  be day/month/year" — never "Invalid input".
- **Plain language, short sentences.** No jargon. Not "submit a case record" —
  "file a report".
- **Predictable and consistent.** Same nav, same button shapes, same words for
  the same things on every page. Surprise is a cost here.
- **Always offer a way out.** Every flow has a visible "save and finish later"
  or "go back". Nothing traps.
- **Warn before anything distressing,** always. Never autoplay, never surprise.
- **Never imply an outcome.** Not "we will find them". Not "no match found".

---

## 5. Visual system

Match the reference design at `docs/Khoj-Design-and-Roadmap.pdf`. Put these in
`static/css/khoj.css` as CSS custom properties on `:root`, and use the tokens
everywhere — no hard-coded colours in templates.

```css
--ground:#f6f8f8;  --surface:#ffffff;  --surface-2:#eef2f2;
--ink:#14201f;     --ink-mid:#3f5150;  --ink-soft:#6b7c7b;
--line:#dbe3e3;    --line-strong:#b9c6c6;
--accent:#0f5257;  --accent-soft:#e2eded;
--amber:#8a5214;   --green:#1b6247;    --red:#8c3030;
```

- **Accent is a deep petrol teal.** Deliberately not the crimson of the flag —
  red reads as alarm, and this page is already someone's worst day.
- **Semantic colours (amber / green / red) are for status only.** Never
  decorative.
- **Type:** Public Sans for the interface — a civic typeface, correct register.
  Noto Sans Devanagari for Nepali. IBM Plex Mono for reference codes. Load from
  Google Fonts with `display=swap` and a real fallback stack.
- Nepali names render in Devanagari beneath the Latin transliteration.
- Dates carry **both** Bikram Sambat and Gregorian: `29 Bhadra 2083 · 29 Aug 2026`.
- Support light and dark via `prefers-color-scheme`, tokens only.

---

## 6. Explicitly do not build

Each of these is a normal good-website feature that is wrong *here*:

| Not this | Because |
|---|---|
| Hero video or background image | Bandwidth. And no image is appropriate over this subject. |
| Count-up number animation | Trivialises the figures. |
| Scroll-triggered fade-ins | Content must exist at rest on slow connections. |
| Parallax, particles, animated gradients | Bandwidth, battery, tone. |
| Testimonial slider | There are no testimonials here, and inventing them would be fabrication. |
| Live JS map with tiles | Fails exactly where it is needed. |
| Chat widget / popup | Third-party JS, and it interrupts. |
| Cookie banner beyond what is legally required | Do not add tracking that needs consent. |
| Newsletter signup | No. |
| Dark patterns of any kind | No. |

---

## 7. Implementation notes

- Template: `registry/templates/registry/home.html`, extending `templates/base.html`.
- Stylesheet: `static/css/khoj.css`. One file. No CSS framework —
  drop the Bootstrap CDN link, this page is hand-built and lighter without it.
- Counts come from the view, cached (`@cache_page` or low-level cache, 5 min).
  Do not run four `COUNT(*)` queries on every anonymous page load.
- **The hero buttons point at named URLs that do not exist yet.** Add stub URL
  patterns and placeholder views in Phase 1 *before* wiring the links, or
  `{% url %}` raises `NoReverseMatch` and the homepage 500s.
- i18n: enable `LocaleMiddleware`, `USE_I18N`, `LOCALE_PATHS`, wrap every
  user-facing string in `{% trans %}` from the start.
- Accessibility is a requirement, not a nice-to-have: semantic landmarks
  (`<header> <main> <nav> <footer>`), one `<h1>`, visible focus states, alt text
  on the SVG, 4.5:1 contrast minimum, 44px minimum tap targets.
- Performance target: **under 100 KB total, first paint under 2 s on simulated
  3G.** If it exceeds that, something on the page does not belong.

---

## 8. Done when

- [ ] Loads and is fully readable with JavaScript disabled.
- [ ] Loads and is fully readable with images disabled.
- [ ] The two hero buttons are the largest tap targets on the page.
- [ ] "You do not need to travel" is visible without scrolling, on a 360px-wide screen.
- [ ] Language toggle switches the page and persists across navigation.
- [ ] Under 100 KB total transfer.
- [ ] Nothing anywhere on the page lists, searches or displays a record.
- [ ] Footer carries the disclaimer and a last-updated timestamp.
- [ ] Keyboard-navigable end to end with a visible focus ring throughout.
- [ ] Legible in both light and dark mode.

---

## Sources behind the decisions here

- Google Person Finder — the two-door entry pattern; the 2010 Pakistan
  deployment failing on lack of connectivity.
- ICRC Restoring Family Links / Trace the Face — tracing service structure.
- NamUs — how a national registry explains itself to a first-time visitor.
- Trauma-informed content design practice — safety, predictability, choice and
  control, non-punitive errors.
- Emergency landing page practice — above-the-fold priority, static maps over
  tile layers, mandatory update timestamps, `tel:` links.

# Build brief — Khoj public landing page (v2)

**For whoever implements this.** Read `CLAUDE.md` first. Build what is specified
here, then stop and show it.

v2 supersedes v1. The earlier version was too plain: it treated "loads on a bad
connection" and "genuinely impressive" as a trade-off. They are not. Everything
below is rich, interactive and modern *and* fits in a quarter of a megabyte,
because it is built from SVG, CSS and about a hundred lines of vanilla
JavaScript rather than from video and frameworks.

---

## 1. Who is looking at this page

Someone who has just learned a person they love is missing, or a relative
helping them. They arrived from a Facebook post. They have never seen this site
and are deciding, in roughly eight seconds, whether it can help them.

The page answers three questions in that time — what is this, can it help me,
what do I do now — and then earns the scroll by teaching them something useful
about how it works.

**Two things this page is not.** It is not a startup launch page: no growth
copy, no "join thousands of users", no confetti. And it is not a brochure: every
interactive thing on it should teach the visitor something they need, rather
than demonstrate that the developer can animate.

That is a higher bar than decoration, not a lower one.

---

## 2. Hard constraints

Break any of these and the page is wrong, however good it looks.

- **No public search over records. No gallery of the recovered. No names, no
  photographs of remains, anywhere on this page.** Counts and aggregates only.
  This will feel like an obvious missing feature. It is refused, not missing —
  see principle 2 in `CLAUDE.md`.
- **No fabricated testimonials, quotes, or survivor stories.** There are no real
  ones, and inventing them over this subject is not a design shortcut, it is a
  lie. Real reported facts, cited, are fine.
- **No donation button or payment flow.**
- **Disclaimer stays in the footer:** reference design, not an official
  registry, seeded fictional data.
- **Content readable with JavaScript off.** JS enhances; it never gates. Every
  interactive component below has a defined no-JS resting state.
- **Nothing parked at `opacity: 0` waiting for an observer.** Animate *from* a
  visible resting state. On a slow connection a reveal that never fires is a
  blank page.
- **Budget: 250 KB total transfer, first contentful paint under 2.5 s on
  simulated 3G.** Generous — but it rules out video and heavy frameworks, which
  is the point. Google Person Finder's 2010 Pakistan deployment is judged a
  failure because the affected population had no connectivity. That is the
  cautionary tale this budget exists for.

---

## 3. Page structure

Eleven bands. Build in order; each is described with its interaction.

### Band 0 — Scroll progress rail *(interactive)*

A thin fixed rail on the left (desktop only, hidden under 900px) with a dot per
band. The dot for the band in view fills; clicking a dot smooth-scrolls to it.
Hovering shows the band name.

Build with `IntersectionObserver` for the active state and
`scroll-behavior: smooth` for the jump. Without JS it simply does not render —
which is fine, because it is navigation, not content.

### Band 1 — Header

Logo `Khoj` with `खोज` beside it. Right side:

- **Language toggle: नेपाली / English.** Not optional. A Nepali family is the
  primary user; an English-only page fails them. Wire through Django i18n
  (`LocaleMiddleware`, `{% trans %}`, `set_language`) from the start — Nepali
  strings may begin as `TODO`, but retrofitting i18n later is far more work.
- **Light / dark toggle**, remembered in `localStorage`, defaulting to
  `prefers-color-scheme`.
- **A telephone number as a `tel:` link.** Some visitors cannot use a web form
  at all. This is a first-class element, not a footer afterthought.
- **Sign in** — quiet text link. Most visitors are not returning users.

**On scroll past the hero**, the header compacts and gains the two primary
action buttons. `position: sticky` plus one class toggled by scroll position.

### Band 2 — Hero *(animated)*

- Headline: **Search for a missing person in one place.**
- Sub: *File one report. Every connected hospital, morgue and police post is
  searched for you, and an official will contact you directly.*

**Behind the type: the convergence animation.** An inline SVG, full-bleed,
low-contrast, sitting behind the text. Two columns of small marks — families on
the left, facilities on the right — with faint curved paths flowing inward to a
single point in the centre. Animate the paths with `stroke-dasharray` +
`stroke-dashoffset` so the flow drifts continuously inward, very slowly, at
around 10–15% opacity.

This is the one ambient flourish on the page, and it earns its place because it
*is* the system: two sides meeting in the middle. Ambient, never attention-
seeking. Under `prefers-reduced-motion: reduce` it renders static.

**Then the two-door split — the most important element on the page.**

| Button | Goes to | Sub-label |
|---|---|---|
| **Someone I know is missing** | family register → report wizard | I want to file a report |
| **I have information about someone** | responder sign-in / access request | I work at a hospital, morgue or police post |

Google Person Finder has used these same two doors since 2010 because every
visitor is one of exactly two people. Largest tap targets on the page by a wide
margin — side by side on desktop, stacked full-width on mobile. Give each a
distinct icon (inline SVG) and a hover state that lifts and deepens the border.

Under them, in plain text: **You do not need to travel.**

That sentence is what the site is *for*. Someone is deciding right now whether
to get on a bus to Pokhara. Do not shrink it, do not move it below the fold.

**No hero video, no photograph, no carousel.** Not austerity — no image is
appropriate over this subject, and video breaks the budget.

### Band 3 — Counters *(animated)*

Four figures: reports filed, records held, people identified, facilities
connected. Real values from the database, cached.

- `font-variant-numeric: tabular-nums`.
- **Count up once on first view**, 700 ms, ease-out. Short and dignified — not a
  slot machine. Skipped entirely under `prefers-reduced-motion`, and the final
  value must be in the HTML so it is correct with JS off.
- Under them: **Last updated 29 Bhadra 2083 · 29 Aug 2026, 14:20.** Emergency
  pages must timestamp themselves; a visitor has no other way to tell live from
  abandoned.

### Band 4 — The problem this solves *(scroll-driven)*

The band that makes someone care. Two states, side by side, revealed as it
enters view:

**Without a registry** — a small map with six district markers and a tangled
path drawn between them, annotated: *Rasuwa → Nuwakot → Chitwan → Nawalpur →
Tanahun → Pokhara. Four days. Hundreds of kilometres. Photographs of 102
unidentified people, viewed by around a thousand searchers a day.*

**With one** — the same map, one marker, one line: *One form. An official
telephones you.*

Animate the tangled path drawing itself with `stroke-dashoffset` when the band
scrolls in, then the single line drawing after it. Resting state (no JS, reduced
motion): both fully drawn, side by side. Still reads perfectly.

These are real reported figures from the August 2026 flood response. Cite them
in small print. Do not embellish and do not add invented detail.

### Band 5 — How it works *(stepper)*

Three steps, click or auto-advance every 6 s, pausing on hover or focus:

1. **You describe them.** What they were wearing, scars or tattoos, where they
   were last seen.
2. **Facilities describe who they have received.** Hospitals, morgues and police
   posts record the same details for people not yet identified.
3. **An official compares the two and contacts you.** Every possible match is
   checked by a trained person before anyone is told anything.

A single inline SVG on the right transitions between three states as the step
changes — left column filling, right column filling, then the two converging.
Keyboard accessible: arrow keys move between steps, `aria-current` on the active
one. Without JS, all three render stacked as a plain numbered list.

Step 3 is doing quiet, essential work: it tells the visitor a human is involved.
That is what makes this trustworthy rather than sinister.

### Band 6 — How a match is found *(the centrepiece — interactive)*

**Build this one properly. It is the single most impressive thing on the page,
and the most useful.**

A miniature, self-contained demo of the matching engine using two obviously
fictional records. The visitor toggles which details are known and watches the
score respond in real time.

- Left: a mock report card with six toggleable attributes — *bird tattoo, left
  forearm* · *red and black checked shirt* · *age 34* · *height ~168 cm* · *last
  seen Timure, Rasuwa* · *male, medium build*.
- Right: a mock unidentified record, fixed, greyed.
- Centre: a score dial or bar, 0–100, animating on every change, with the
  six-way breakdown lighting up beneath it: `marks 25/25`, `clothing 18/20`,
  `age 18/18`, `geography 13/15`, `height 8/12`, `sex & build 4/10`.
- Beneath: a line that updates with the total — *below 30: not stored* · *30–55:
  weak candidate* · *above 55: sent to a verifier*.
- Turn off the tattoo and the score visibly collapses. That is the lesson.

Weights are in `CLAUDE.md` §Matching engine. Hard-code them in the JS; this is a
teaching toy, not a call to the real engine.

**Why it belongs here rather than being a gimmick:** it teaches the visitor,
before they reach the form, that a tattoo is worth more than a height estimate —
and that is exactly what makes the report they go on to file more useful. It
also quietly demonstrates that the system is a transparent scoring function, not
a black box, which is the whole ethical posture of the project.

Without JS: renders as a static table of the six signals and their weights.

### Band 7 — What helps us find someone

Four cards, ordered by how much they actually help, each with an inline SVG icon
and a hover lift:

- **Scars, tattoos, dental work** — the most identifying detail there is.
- **What they were wearing** — colours and patterns, as you remember them.
- **Where and when you last saw them** — a place name and roughly what time.
- **A clear photograph** — face visible, any age.

Then, prominently: **If you are not sure about something, leave it blank.
A guess is worse than a gap.**

### Band 8 — Where we are connected *(interactive map)*

Answers "is the hospital my brother might be in part of this?"

- An **inline SVG map** of the affected districts. Hover or tap a district and a
  side panel lists the facilities connected there with their record counts.
  Active district highlights; panel updates. Keyboard reachable — each district
  is a `<button>` in the tab order.
- **Inline SVG, not Leaflet, not tiles.** Cell service is unreliable in exactly
  the places this matters, and a map that must fetch tiles is a map that does
  not load. An inline SVG also prints.
- Below it, the full facility list grouped by district — Rasuwa, Nuwakot,
  Chitwan, Nawalpur, Tanahun, Kaski — so the information exists without the map.
- A line for facilities not yet connected, with a contact route.

### Band 9 — What happens to what you tell us

Trust band. Four short commitments, plainly worded:

- Your report is visible to you and to the officials reviewing possible matches.
  Nobody else.
- Photographs are never shown publicly and never shown to other families.
- Every time an official opens a record it is recorded — who, and when.
- You can withdraw your report at any time.

**No lock icons, no shield graphics.** Plain sentences carry more weight here;
security iconography reads as marketing and undercuts the point.

### Band 10 — If you cannot use this website

Directly addresses the population Person Finder lost in 2010.

- **Telephone** — large, `tel:` link, with hours.
- **In person** — help desks with locations.
- **Someone can file on your behalf** — a relative, neighbour or volunteer.
  Say explicitly that this is allowed and normal.

### Band 11 — Questions *(accordion)*

`<details>` / `<summary>` — native HTML, works without JS, accessible for free.
Do not hand-roll this. Animate the open/close height with CSS.

Ask the questions people actually have, including the uncomfortable ones:

- Will you show me photographs of bodies?
- What happens if the match is wrong?
- How long does this take?
- Is this the government?
- What if I do not know my relative's exact age or height?
- Can I file a report for a neighbour?
- What happens after someone is identified?

Answer plainly. Never promise an outcome.

### Footer

Contact, language and theme toggles, disclaimer, last-updated timestamp,
sources for the figures used in Band 4.

---

## 4. Interaction inventory

Everything interactive on the page, and what it costs:

| Component | Built with | No-JS state |
|---|---|---|
| Scroll progress rail | IntersectionObserver | not rendered |
| Sticky compacting header | CSS sticky + 1 class toggle | static header |
| Hero convergence animation | SVG + CSS `stroke-dashoffset` | static SVG |
| Counter count-up | ~15 lines JS | final numbers in HTML |
| Problem/solution path draw | SVG + CSS keyframes | both paths drawn |
| How-it-works stepper | ~25 lines JS | three steps stacked |
| **Match demo** | ~40 lines JS | static weights table |
| District map | ~15 lines JS | full facility list below |
| FAQ accordion | native `<details>` | works natively |
| Theme toggle | ~10 lines JS + localStorage | follows OS setting |
| Language toggle | Django i18n form POST | works — server-side |

Total JavaScript: roughly 120 lines of vanilla ES6. **No framework, no jQuery,
no animation library.** Everything above is achievable with the platform, and a
framework would cost more bytes than the entire rest of the page.

---

## 5. Content rules

These govern every word. They come from trauma-informed content design practice
and are requirements, not preferences.

- **No urgency pressure.** No countdowns, no "act now", no red banners. The
  visitor is under more pressure than any interface can add.
- **No blame in errors.** "That date doesn't look right — it should be
  day/month/year", never "Invalid input".
- **Plain language, short sentences.** "File a report", not "submit a case
  record".
- **Predictable.** Same words for the same things everywhere. Surprise is a cost.
- **Always a way out.** Every flow has a visible "save and finish later".
- **Never imply an outcome.** Not "we will find them". Not "no match found".

---

## 6. Visual system

Tokens go in `static/css/khoj.css` on `:root`. No hard-coded colours in
templates.

```css
--ground:#f6f8f8;  --surface:#ffffff;  --surface-2:#eef2f2;
--ink:#14201f;     --ink-mid:#3f5150;  --ink-soft:#6b7c7b;
--line:#dbe3e3;    --line-strong:#b9c6c6;
--accent:#0f5257;  --accent-soft:#e2eded;
--amber:#8a5214;   --green:#1b6247;    --red:#8c3030;
```

- **Accent is a deep petrol teal.** Deliberately not the crimson of the flag —
  red reads as alarm, and this page is already someone's worst day.
- **Semantic colours (amber / green / red) signal status only.** Never decorative.
- **Type:** Public Sans for the interface — a civic typeface, correct register.
  Noto Sans Devanagari for Nepali. IBM Plex Mono for reference codes. Google
  Fonts, `display=swap`, real fallback stacks.
- Nepali names in Devanagari beneath the Latin transliteration.
- Dates carry both calendars: `29 Bhadra 2083 · 29 Aug 2026`.
- Full light and dark support through the tokens.
- Motion: 200–300 ms, ease-out, and **every animation wrapped in a
  `prefers-reduced-motion: reduce` guard.**

Reference: `docs/Khoj-Design-and-Roadmap.pdf`.

---

## 7. Do not build

Each is a normal good-website feature that is wrong *here*:

| Not this | Because |
|---|---|
| Hero video or photograph | Budget, and no image is appropriate over this subject |
| Testimonial slider | No real ones exist; inventing them is fabrication |
| Live JS map with tiles | Fails exactly where it is needed most |
| Chat widget / popup | Third-party JS, and it interrupts |
| Newsletter signup | No |
| Animation library (GSAP, AOS, Lottie) | Costs more than the whole page; CSS does all of this |
| CSS framework | Hand-built is lighter and this page is bespoke |
| Anything that lists, searches or shows a record | The one rule that cannot bend |

---

## 8. Implementation notes

- Template `registry/templates/registry/home.html`, extending
  `templates/base.html`. Split the bands into
  `registry/templates/registry/_band_*.html` includes — an eleven-band page in
  one file is unmaintainable.
- One stylesheet, `static/css/khoj.css`. One script,
  `static/js/khoj.js`, deferred.
- Counts come from the view, cached 5 minutes. Do not run four `COUNT(*)`
  queries on every anonymous page load.
- Hero buttons point at `{% url 'register' %}` and `{% url 'login' %}` — both
  exist as of Phase 1.
- i18n: `LocaleMiddleware`, `USE_I18N`, `LOCALE_PATHS`, every user-facing string
  in `{% trans %}`.
- Accessibility is a requirement: semantic landmarks, one `<h1>`, visible focus
  rings, `<title>` on every SVG, 4.5:1 contrast minimum, 44px tap targets,
  keyboard reachable end to end.

---

## 9. Done when

- [ ] Readable and usable with JavaScript disabled.
- [ ] Readable with images disabled.
- [ ] The two hero buttons are the largest tap targets on the page.
- [ ] "You do not need to travel" visible without scrolling at 360px wide.
- [ ] The match demo responds instantly and the score visibly collapses when the
      tattoo is switched off.
- [ ] Every animation stops under `prefers-reduced-motion: reduce`.
- [ ] Language toggle switches the page and persists across navigation.
- [ ] Under 250 KB total transfer.
- [ ] Nothing anywhere lists, searches or displays a record.
- [ ] Keyboard-navigable end to end with a visible focus ring throughout.
- [ ] Legible in both light and dark mode.

---

## Sources behind these decisions

- Google Person Finder — the two-door entry pattern; the 2010 Pakistan
  deployment failing on lack of connectivity.
- ICRC Restoring Family Links / Trace the Face — tracing service structure.
- NamUs — how a national registry explains itself to a first-time visitor.
- Trauma-informed content design — safety, predictability, choice and control,
  non-punitive errors.
- Emergency landing page practice — above-the-fold priority, static maps over
  tile layers, mandatory update timestamps, `tel:` links.
- Kathmandu Post and myRepublica reporting, Aug 2026 — the figures in Band 4.

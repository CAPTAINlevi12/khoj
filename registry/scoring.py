"""The matching engine.

Pure Python. Nothing in this module imports Django, which is deliberate:
every rule here can be exercised by a unit test with plain values, no
database and no request. It also keeps the domain logic separable from the
framework — the thing that makes it possible to say what the engine does
without reading a view.

A scoring function, not a machine-learning model. Every point must be
explainable aloud in a courtroom, which is why the output is a number AND a
breakdown naming the rule that produced each part.

Weights come from CLAUDE.md and total 100:

    distinguishing marks   25    near-unique when present
    clothing               20    specific and memorable
    age                    18    stated age against an estimated band
    geography and time     15    rule depends on the kind of disaster
    height                 12    family estimates are unreliable
    sex and build          10    post-mortem estimates get revised
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

MAX_POINTS = {
    "marks": 25,
    "clothing": 20,
    "age": 18,
    "geography": 15,
    "height": 12,
    "sex_build": 10,
}

# Thresholds, from the design spec.
DISCARD_BELOW = 30
WEAK_UPTO = 55
ALWAYS_SURFACE_MARKS_ABOVE = 15

# Words that carry no identifying information, so counting them would inflate
# every comparison equally and tell us nothing.
STOPWORDS = {
    "a", "an", "and", "the", "with", "of", "in", "on", "or", "was", "were",
    "wearing", "worn", "his", "her", "their", "some", "very", "colour", "color",
}

# Spelling and vocabulary variants normalised to one token, so "maroon kurta"
# and "dark red kurta" are not treated as unrelated.
SYNONYMS = {
    "maroon": "red", "crimson": "red", "scarlet": "red",
    "navy": "blue", "indigo": "blue",
    "grey": "gray",
    "trousers": "trouser", "pants": "trouser", "jeans": "denim",
    "tshirt": "shirt", "t": "", "shirts": "shirt",
    "sandals": "sandal", "shoes": "shoe", "slippers": "sandal",
    "tattoos": "tattoo", "scars": "scar", "marks": "mark",
}


def tokenise(text: str) -> set[str]:
    """Words worth comparing, normalised.

    Lowercased, punctuation stripped, stopwords dropped and synonyms folded
    together. Returns a set because repetition is not evidence: saying "red"
    twice does not make a shirt redder.
    """
    if not text:
        return set()
    words = re.findall(r"[a-z]+", text.lower())
    out = set()
    for word in words:
        word = SYNONYMS.get(word, word)
        if word and word not in STOPWORDS and len(word) > 1:
            out.add(word)
    return out


def overlap_ratio(left: str, right: str) -> float:
    """How much two free-text descriptions agree, 0.0 to 1.0.

    The denominator is the SMALLER token set, not the union. A mortuary note
    reading "tattoo, bird, left forearm" and a family's longer paragraph
    describing the same tattoo should score high — the shorter description
    being less detailed is not disagreement.
    """
    a, b = tokenise(left), tokenise(right)
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


@dataclass
class Side:
    """One person as described by one side of the system.

    Plain values only — no model instances — so this module never has to know
    that Django exists.
    """

    age: int | None = None
    age_min: int | None = None
    age_max: int | None = None
    sex: str = "UNKNOWN"
    height_cm: int | None = None
    build: str = "UNKNOWN"
    clothing: str = ""
    marks: str = ""
    flow_order: int | None = None
    region_id: int | None = None
    at: object | None = None          # datetime, kept opaque on purpose


@dataclass
class Result:
    total: int
    breakdown: dict[str, int] = field(default_factory=dict)
    reasons: dict[str, str] = field(default_factory=dict)

    @property
    def band(self) -> str:
        """What happens to this pair.

        A strong marks hit always surfaces regardless of the total: a tattoo
        match outranks every other disagreement.
        """
        if self.breakdown.get("marks", 0) > ALWAYS_SURFACE_MARKS_ABOVE:
            return "surface"
        if self.total > WEAK_UPTO:
            return "surface"
        if self.total >= DISCARD_BELOW:
            return "weak"
        return "discard"

    @property
    def is_worth_storing(self) -> bool:
        """Below the discard line no row is written at all.

        Three thousand reports against a thousand records is three million
        pairs; storing the ones nobody will ever look at is what makes the
        table unusable.
        """
        return self.band != "discard"


# --------------------------------------------------------------- signals


def score_marks(report: Side, record: Side) -> tuple[int, str]:
    """Scars, tattoos, dental work. Weighted highest because near-unique."""
    ratio = overlap_ratio(report.marks, record.marks)
    points = round(MAX_POINTS["marks"] * ratio)
    if not report.marks or not record.marks:
        return 0, "no distinguishing marks recorded on one side"
    shared = sorted(tokenise(report.marks) & tokenise(record.marks))
    if not shared:
        return 0, "no marks in common"
    return points, f"marks in common: {', '.join(shared)}"


def score_clothing(report: Side, record: Side) -> tuple[int, str]:
    ratio = overlap_ratio(report.clothing, record.clothing)
    points = round(MAX_POINTS["clothing"] * ratio)
    if not report.clothing or not record.clothing:
        return 0, "no clothing recorded on one side"
    shared = sorted(tokenise(report.clothing) & tokenise(record.clothing))
    if not shared:
        return 0, "no clothing in common"
    return points, f"clothing in common: {', '.join(shared)}"


def score_age(report: Side, record: Side) -> tuple[int, str]:
    """A stated age against an estimated band.

    Full points inside the band, decaying outside it. A 34-year-old against
    an estimate of 30-40 is a match; against 60-70 it is not.
    """
    age, low, high = report.age, record.age_min, record.age_max
    if age is None or (low is None and high is None):
        return 0, "age not known on one side"

    low = low if low is not None else high
    high = high if high is not None else low

    if low <= age <= high:
        return MAX_POINTS["age"], f"age {age} falls inside the estimate {low}-{high}"

    distance = low - age if age < low else age - high
    # Ten years outside the band takes the score to nothing.
    ratio = max(0.0, 1 - distance / 10)
    points = round(MAX_POINTS["age"] * ratio)
    return points, f"age {age} is {distance} years outside the estimate {low}-{high}"


def score_height(report: Side, record: Side) -> tuple[int, str]:
    """Full points within 4 cm, decaying to zero at 15 cm.

    Modest weight and a wide tolerance because a family's height is usually a
    guess, while the mortuary's is a measurement.
    """
    a, b = report.height_cm, record.height_cm
    if a is None or b is None:
        return 0, "height not known on one side"

    difference = abs(a - b)
    if difference <= 4:
        return MAX_POINTS["height"], f"heights agree within {difference} cm"
    if difference >= 15:
        return 0, f"heights differ by {difference} cm"

    ratio = 1 - (difference - 4) / 11
    return round(MAX_POINTS["height"] * ratio), f"heights differ by {difference} cm"


def score_sex_build(report: Side, record: Side) -> tuple[int, str]:
    """Soft on purpose — post-mortem estimates are frequently revised.

    Note this is a partial signal, not a gate: a disagreement here reduces the
    score, it does not veto the pair.
    """
    points, notes = 0, []

    known = {report.sex, record.sex} - {"UNKNOWN", ""}
    if len(known) and report.sex == record.sex and report.sex != "UNKNOWN":
        points += 6
        notes.append("sex agrees")
    elif report.sex != "UNKNOWN" and record.sex != "UNKNOWN":
        notes.append("sex differs")

    if report.build == record.build and report.build != "UNKNOWN":
        points += 4
        notes.append("build agrees")

    return points, "; ".join(notes) or "sex and build not known"


def score_geography(report: Side, record: Side, rule: str) -> tuple[int, str]:
    """The signal whose RULE depends on the kind of disaster.

    downstream — flood, glacier collapse. Water goes one way, so a body
        recovered upstream of the last-seen point is not that person, and
        scores zero however well everything else agrees.
    downslope — landslide. Same reasoning, different force.
    proximity — earthquake, fire. Nothing drifts; being in the same place is
        the whole signal.
    """
    max_points = MAX_POINTS["geography"]

    if rule in {"downstream", "downslope"}:
        seen, found = report.flow_order, record.flow_order
        if seen is None or found is None:
            return 0, "position along the watercourse not known"
        if found < seen:
            direction = "upstream" if rule == "downstream" else "uphill"
            return 0, f"recovered {direction} of the last-seen point"
        drift = found - seen
        if drift == 0:
            return max_points, "recovered in the district last seen in"
        # Plausible drift decays with distance; three districts is the limit.
        ratio = max(0.0, 1 - (drift - 1) / 3)
        word = "downstream" if rule == "downstream" else "downslope"
        return round(max_points * ratio), f"recovered {drift} district(s) {word}"

    # proximity
    if report.region_id is None or record.region_id is None:
        return 0, "district not known on one side"
    if report.region_id == record.region_id:
        return max_points, "recovered in the district last seen in"
    return 0, "recovered in a different district"


def score(report: Side, record: Side, rule: str = "proximity") -> Result:
    """Score one pair. The only entry point anything outside this module needs."""
    signals = {
        "marks": score_marks(report, record),
        "clothing": score_clothing(report, record),
        "age": score_age(report, record),
        "geography": score_geography(report, record, rule),
        "height": score_height(report, record),
        "sex_build": score_sex_build(report, record),
    }

    breakdown = {name: points for name, (points, _) in signals.items()}
    reasons = {name: why for name, (_, why) in signals.items()}
    return Result(total=sum(breakdown.values()), breakdown=breakdown, reasons=reasons)

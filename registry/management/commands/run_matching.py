"""Score every open report against every open record, one event at a time.

Run with:  python manage.py run_matching
           python manage.py run_matching --event bhotekoshi-2026

Kept a management command rather than a signal or a request-time hook: this
is a batch job over the whole table, it takes as long as it takes, and it
must be runnable by hand after a rule changes.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from registry.models import Event, MatchCandidate, MissingPersonReport, UnidentifiedRecord
from registry.scoring import Side, score


def side_from_report(report):
    """Translate a Django model into the plain values the engine takes.

    This function is the entire boundary between the framework and the domain
    logic. Because it exists, scoring.py never imports Django and can be
    tested with dictionaries.
    """
    return Side(
        age=report.age,
        sex=report.sex,
        height_cm=report.height_cm,
        build=report.build,
        clothing=report.clothing_description,
        marks=report.distinguishing_marks,
        flow_order=report.last_seen_region.flow_order if report.last_seen_region else None,
        region_id=report.last_seen_region_id,
        at=report.last_seen_at,
    )


def side_from_record(record):
    return Side(
        age_min=record.estimated_age_min,
        age_max=record.estimated_age_max,
        sex=record.sex,
        height_cm=record.height_cm,
        build=record.build,
        clothing=record.clothing_description,
        marks=record.distinguishing_marks,
        flow_order=record.recovery_region.flow_order if record.recovery_region else None,
        region_id=record.recovery_region_id,
        at=record.recovered_at,
    )


class Command(BaseCommand):
    help = "Score reports against unidentified records and store the candidates."

    def add_arguments(self, parser):
        parser.add_argument("--event", help="Event slug. Defaults to the primary event.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Score and report, but write nothing.",
        )

    def handle(self, *args, **options):
        if options["event"]:
            events = Event.objects.filter(slug=options["event"])
        else:
            events = Event.objects.filter(is_primary=True)

        if not events.exists():
            self.stderr.write("No matching event.")
            return

        for event in events:
            self.run_for_event(event, dry_run=options["dry_run"])

    def run_for_event(self, event, dry_run=False):
        # Scoped to ONE event. A Nepali report must never be compared against
        # Turkish remains, and partitioning this way is also what keeps
        # reports x records tractable.
        reports = list(
            MissingPersonReport.objects.filter(
                event=event,
                status__in=[
                    MissingPersonReport.Status.SEARCHING,
                    MissingPersonReport.Status.UNDER_REVIEW,
                ],
            ).select_related("last_seen_region")
        )
        records = list(
            UnidentifiedRecord.objects.filter(
                event=event,
                status__in=[
                    UnidentifiedRecord.Status.HELD,
                    UnidentifiedRecord.Status.UNDER_REVIEW,
                ],
            ).select_related("recovery_region")
        )

        rule = event.geography_rule
        self.stdout.write(
            f"{event.name}: {len(reports)} reports x {len(records)} records "
            f"= {len(reports) * len(records)} pairs, geography rule '{rule}'"
        )

        stored, discarded = [], 0

        for report in reports:
            left = side_from_report(report)
            for record in records:
                result = score(left, side_from_record(record), rule)

                if not result.is_worth_storing:
                    # Below 30 no row is written at all. Otherwise three
                    # thousand reports against a thousand records is three
                    # million rows nobody will ever look at.
                    discarded += 1
                    continue

                stored.append((report, record, result))

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"dry run: {len(stored)} would be stored, {discarded} discarded"
                )
            )
            for report, record, result in sorted(stored, key=lambda s: -s[2].total)[:10]:
                self.stdout.write(
                    f"  {result.total:3d}  {result.band:8s}  "
                    f"{report.reference} <-> {record.custody_reference}"
                )
            return

        # One transaction: either the whole run lands or none of it does, so a
        # verifier never sees a half-written queue.
        with transaction.atomic():
            for report, record, result in stored:
                MatchCandidate.objects.update_or_create(
                    report=report,
                    record=record,
                    defaults={
                        "event": event,
                        "score": result.total,
                        "score_breakdown": result.breakdown,
                        "score_reasons": result.reasons,
                    },
                )

        surfaced = sum(1 for _, _, r in stored if r.band == "surface")
        self.stdout.write(
            self.style.SUCCESS(
                f"stored {len(stored)} candidates ({surfaced} above the review "
                f"threshold), discarded {discarded}"
            )
        )

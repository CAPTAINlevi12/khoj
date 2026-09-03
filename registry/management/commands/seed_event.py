"""Load the worked example: the August 2026 Bhotekoshi flood.

Nepal is the case study this system was designed against, not the system's
subject. It loads as one row here; a deployment for another disaster adds
another row and touches no code.

Run with:  python manage.py seed_event
"""

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from registry.models import Event, Organisation, Region

# SVG paths are in the coverage map's 420x250 viewBox. Shapes are indicative,
# not survey data — this is seeded fictional content.
DISTRICTS = [
    {
        "name": "Rasuwa",
        "map_path": "M30 40 L120 25 L180 55 L150 120 L60 130 Z",
        "label": (105, 80),
        "organisations": [
            ("Dhunche District Hospital", Organisation.Kind.HOSPITAL),
            ("Rasuwa District Police Office", Organisation.Kind.POLICE_POST),
            ("Timure Health Post", Organisation.Kind.HOSPITAL),
        ],
    },
    {
        "name": "Nuwakot",
        "map_path": "M180 55 L280 40 L330 90 L250 115 Z",
        "label": (255, 80),
        "organisations": [
            ("Trishuli District Hospital", Organisation.Kind.HOSPITAL),
            ("Betrawati Police Post", Organisation.Kind.POLICE_POST),
        ],
    },
    {
        "name": "Chitwan",
        "map_path": "M60 130 L150 120 L170 190 L80 200 Z",
        "label": (115, 165),
        "organisations": [
            ("Bharatpur Hospital", Organisation.Kind.HOSPITAL),
            ("Chitwan Medical College", Organisation.Kind.HOSPITAL),
        ],
    },
    {
        "name": "Kaski",
        "map_path": "M170 190 L250 115 L330 90 L340 175 L250 200 Z",
        "label": (265, 155),
        "organisations": [
            ("Pokhara Academy of Health Sciences", Organisation.Kind.HOSPITAL),
            ("Gandaki Medical College", Organisation.Kind.HOSPITAL),
            ("Kaski District Police Office", Organisation.Kind.POLICE_POST),
        ],
    },
]


class Command(BaseCommand):
    help = "Seed the Bhotekoshi flood event, its districts and facilities."

    @transaction.atomic
    def handle(self, *args, **options):
        nepal, _ = Region.objects.get_or_create(
            name="Nepal", kind=Region.Kind.COUNTRY
        )

        event, created = Event.objects.get_or_create(
            slug="bhotekoshi-2026",
            defaults={
                "name": "Bhotekoshi and Trishuli flood",
                "kind": Event.Kind.GLACIER_COLLAPSE,
                "status": Event.Status.ACTIVE,
                "occurred_on": date(2026, 8, 26),
                "is_primary": True,
                "summary": (
                    "A glacier collapse on the north face of Langtang-Lirung sent a "
                    "debris flow down the Bhotekoshi and Trishuli valleys, across "
                    "Rasuwa and Nuwakot."
                ),
            },
        )

        for spec in DISTRICTS:
            region, _ = Region.objects.get_or_create(
                name=spec["name"],
                kind=Region.Kind.DISTRICT,
                defaults={"parent": nepal},
            )
            region.map_path = spec["map_path"]
            region.label_x, region.label_y = spec["label"]
            region.parent = nepal
            region.save()

            event.regions.add(region)

            for org_name, org_kind in spec["organisations"]:
                Organisation.objects.get_or_create(
                    name=org_name,
                    defaults={"kind": org_kind, "region": region},
                )

        verb = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb} {event.name} — "
                f"{event.regions.count()} districts, "
                f"{Organisation.objects.filter(region__events=event).count()} facilities."
            )
        )

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D
from django.core.management.base import BaseCommand

from campaigns.models import PetitionSignature
from pbaabp.email import send_email_message

GEOJSON = """
{
  "type": "LineString",
  "coordinates": [
    [
      -75.21601480145434,
      39.94316554140741
    ],
    [
      -75.21135446997803,
      39.94635035787846
    ],
    [
      -75.20582524727271,
      39.94150424312116
    ],
    [
      -75.21127000972733,
      39.93884746506717
    ],
    [
      -75.21602046867147,
      39.943156412515634
    ]
  ]
}
"""

geom = GEOSGeometry(GEOJSON)
geom.srid = 4326
SENT = []


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("email_template", nargs="?", type=str)
        parser.add_argument(
            "--buffer-meters",
            type=int,
            default=300,
            help="Send to profiles within this many meters of the corridor",
        )

    def handle(self, *args, **options):
        settings.EMAIL_SUBJECT_PREFIX = ""
        signatures = PetitionSignature.objects.filter(
            petition__slug="parking-protected-bike-lane-47th",
            location__distance_lte=(geom, D(m=options["buffer_meters"])),
        )
        print("Petition signatures!")
        for signature in signatures:
            if signature.email and signature.email.lower() not in SENT:
                send_email_message(
                    "48th-woodland-safety",
                    "Philly Bike Action <noreply@bikeaction.org>",
                    [signature.email],
                    {"first_name": signature.first_name, "petition": True},
                    reply_to=["district3@bikeaction.org"],
                )
                SENT.append(signature.email.lower())
            else:
                print(f"skipping {signature}")
        print(len(SENT))

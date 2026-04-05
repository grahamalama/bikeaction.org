from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand

from pbaabp.email import send_email_message
from profiles.models import Profile

GEOJSON = """
      {
        "coordinates": [
          [
            [
              -75.13086773335263,
              39.95964364701044
            ],
            [
              -75.10819043717983,
              39.97315884118123
            ],
            [
              -75.07268496818497,
              39.98212302964217
            ],
            [
              -75.04635329086702,
              40.01297921299391
            ],
            [
              -75.01415015564582,
              40.021704790164534
            ],
            [
              -74.97642903210733,
              40.05006900696134
            ],
            [
              -75.01402742198854,
              40.07218182942253
            ],
            [
              -75.13177325999067,
              39.98638655761218
            ],
            [
              -75.14873017340292,
              39.98853532435254
            ],
            [
              -75.15445062897481,
              39.961746756943
            ],
            [
              -75.13086773335263,
              39.95964364701044
            ]
          ]
        ],
        "type": "Polygon"
      }
"""

geom = GEOSGeometry(GEOJSON)

profiles = Profile.objects.filter(location__within=geom)
SENT = []


class Command(BaseCommand):
    def handle(self, *args, **options):
        settings.EMAIL_SUBJECT_PREFIX = ""
        for profile in profiles:
            if profile.user.email not in SENT:
                send_email_message(
                    "trails-master-plan-survey",
                    "Philly Bike Action <noreply@bikeaction.org>",
                    [profile.user.email],
                    {"profile": profile},
                    reply_to=["district1@bikeaction.org", "district6@bikeaction.org"],
                )
                SENT.append(profile.user.email)
            else:
                print(f"skipping {profile}")
        print(len(SENT))

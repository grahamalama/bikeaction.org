from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from profiles.models import Profile
from profiles.signals import ORGANIZER_GROUP_NAME


class Command(BaseCommand):
    help = "Sync the Organizers group membership with profile.is_organizer."

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name=ORGANIZER_GROUP_NAME)
        added = removed = 0
        for profile in Profile.objects.select_related("user").all():
            in_group = profile.user.groups.filter(pk=group.pk).exists()
            if profile.is_organizer and not in_group:
                profile.user.groups.add(group)
                added += 1
            elif not profile.is_organizer and in_group:
                profile.user.groups.remove(group)
                removed += 1
        self.stdout.write(self.style.SUCCESS(f"Added {added}, removed {removed}."))

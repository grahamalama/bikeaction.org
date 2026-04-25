from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import Group
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from facets.models import District
from profiles.tasks import add_user_to_connected_role, remove_user_from_connected_role

ORGANIZER_GROUP_NAME = "Organizers"


@receiver(post_save, sender=SocialAccount, dispatch_uid="social_account_post_save")
def social_account_post_save(sender, instance, **kwargs):
    if instance.provider == "discord":
        add_user_to_connected_role.delay(instance.uid)


@receiver(post_delete, sender=SocialAccount, dispatch_uid="social_account_post_delete")
def social_account_post_delete(sender, instance, **kwargs):
    if instance.provider == "discord":
        remove_user_from_connected_role.delay(instance.uid)


def _sync_organizer_group(profile):
    group, _ = Group.objects.get_or_create(name=ORGANIZER_GROUP_NAME)
    if profile.is_organizer:
        profile.user.groups.add(group)
    else:
        profile.user.groups.remove(group)


@receiver(
    post_save,
    sender=District.organizers.through,
    dispatch_uid="district_organizers_through_post_save",
)
def district_organizers_through_post_save(sender, instance, **kwargs):
    _sync_organizer_group(instance.profile)


@receiver(
    post_delete,
    sender=District.organizers.through,
    dispatch_uid="district_organizers_through_post_delete",
)
def district_organizers_through_post_delete(sender, instance, **kwargs):
    _sync_organizer_group(instance.profile)

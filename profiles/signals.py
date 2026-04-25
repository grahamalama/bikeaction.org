from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import Group
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from facets.models import District
from profiles.models import Profile
from profiles.tasks import add_user_to_connected_role, remove_user_from_connected_role

ORGANIZER_GROUP_NAME = "Organizers"

_pending_clear_profiles: dict[int, list] = {}


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
    m2m_changed,
    sender=District.organizers.through,
    dispatch_uid="district_organizers_changed",
)
def district_organizers_changed(sender, instance, action, reverse, pk_set, **kwargs):
    if action == "pre_clear":
        if reverse:
            _pending_clear_profiles[id(instance)] = [instance]
        else:
            _pending_clear_profiles[id(instance)] = list(instance.organizers.all())
        return

    if action not in {"post_add", "post_remove", "post_clear"}:
        return

    if action == "post_clear":
        profiles = _pending_clear_profiles.pop(id(instance), [])
    elif reverse:
        profiles = [instance]
    else:
        profiles = Profile.objects.filter(pk__in=pk_set or [])

    for profile in profiles:
        _sync_organizer_group(profile)

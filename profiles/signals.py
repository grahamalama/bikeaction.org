from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from facets.models import District
from profiles.models import Profile
from profiles.tasks import add_user_to_connected_role, remove_user_from_connected_role

ORGANIZER_GROUP_NAME = "Organizers"
ORGANIZER_PERM_CODENAME = "can_organize"
ORGANIZER_PERM_APP_LABEL = "profiles"


@receiver(post_save, sender=SocialAccount, dispatch_uid="social_account_post_save")
def social_account_post_save(sender, instance, **kwargs):
    if instance.provider == "discord":
        add_user_to_connected_role.delay(instance.uid)


@receiver(post_delete, sender=SocialAccount, dispatch_uid="social_account_post_delete")
def social_account_post_delete(sender, instance, **kwargs):
    if instance.provider == "discord":
        remove_user_from_connected_role.delay(instance.uid)


def _ensure_organizer_group():
    """Idempotently ensures the Organizers group exists and holds the
    `profiles.can_organize` permission. Safe to call repeatedly."""
    group, _ = Group.objects.get_or_create(name=ORGANIZER_GROUP_NAME)
    try:
        perm = Permission.objects.get(
            codename=ORGANIZER_PERM_CODENAME,
            content_type__app_label=ORGANIZER_PERM_APP_LABEL,
        )
    except Permission.DoesNotExist:
        return group
    group.permissions.add(perm)
    return group


def _sync_organizer_group(profile):
    group = _ensure_organizer_group()
    if profile.is_organizer:
        profile.user.groups.add(group)
    else:
        profile.user.groups.remove(group)


def _schedule_organizer_sync(profile_id):
    def _run():
        try:
            _sync_organizer_group(Profile.objects.get(pk=profile_id))
        except Profile.DoesNotExist:
            pass

    transaction.on_commit(_run)


@receiver(
    post_save,
    sender=District.organizers.through,
    dispatch_uid="district_organizers_through_post_save",
)
def district_organizers_through_post_save(sender, instance, **kwargs):
    _schedule_organizer_sync(instance.profile_id)


@receiver(
    post_delete,
    sender=District.organizers.through,
    dispatch_uid="district_organizers_through_post_delete",
)
def district_organizers_through_post_delete(sender, instance, **kwargs):
    _schedule_organizer_sync(instance.profile_id)


@receiver(
    m2m_changed,
    sender=District.organizers.through,
    dispatch_uid="district_organizers_m2m_changed",
)
def district_organizers_m2m_changed(sender, instance, action, reverse, pk_set, **kwargs):
    if action not in {"post_add", "post_remove"}:
        return
    if reverse:
        _schedule_organizer_sync(instance.pk)
    else:
        for pk in pk_set or []:
            _schedule_organizer_sync(pk)

from django.db.models.signals import post_save
from django.dispatch import receiver
from director.models import User, Director, ContactModel
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        content_type = ContentType.objects.get_for_model(Director)
        permission = Permission.objects.get(content_type=content_type, codename='is_director')
        dir_user = Director.objects.create(user=instance)
        contact_model = ContactModel.objects.create(director=dir_user)
        dir_user.user.user_permissions.add(permission)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    try:
        instance.director.save()
    except Exception:
        pass

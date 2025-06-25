# services/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from services.models.access_control import UserServiceAccess

User = get_user_model()

@receiver(post_save, sender=User)
def create_service_access_for_superuser(sender, instance, created, **kwargs):
    if created and instance.is_superuser:
        UserServiceAccess.objects.update_or_create(
            user=instance,
            defaults={field.name: True for field in UserServiceAccess._meta.fields if field.name.startswith("can_access_")}
        )

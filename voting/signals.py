from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import VoterProfile, CandidateProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create profile when user role is assigned"""
    if created:
        if instance.role == 'voter':
            VoterProfile.objects.get_or_create(user=instance)
        elif instance.role == 'candidate':
            CandidateProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Update profile when user role changes"""
    if instance.role == 'voter':
        VoterProfile.objects.get_or_create(user=instance)
    elif instance.role == 'candidate':
        CandidateProfile.objects.get_or_create(user=instance)
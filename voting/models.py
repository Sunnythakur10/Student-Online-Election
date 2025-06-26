from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('voter', 'Voter'),
        ('candidate', 'Candidate'),
        ('admin', 'Admin'),
    )

    BRANCH_CHOICES = [
        ('CSE', 'Computer Science'),
        ('ECE', 'Electronics and Communication'),
        ('ME', 'Mechanical'),
        ('CE', 'Civil'),
        ('EE', 'Electrical'),
    ]

    YEAR_CHOICES = [
        ('1', 'First Year'),
        ('2', 'Second Year'),
        ('3', 'Third Year'),
        ('4', 'Fourth Year'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='voter')
    email = models.EmailField(unique=True)
    branch = models.CharField(max_length=50, choices=BRANCH_CHOICES, default='CSE')
    year_of_study = models.CharField(max_length=1, choices=YEAR_CHOICES, default='1')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.role})"


class VoterProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    has_voted = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Voter: {self.user.username}"


class CandidateProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    manifesto = models.TextField(blank=True, help_text="Your campaign manifesto and promises")
    slogan = models.CharField(max_length=200, blank=True, help_text="Campaign slogan or motto")
    votes_received = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Candidate: {self.user.username}"
    
    def update_vote_count(self):
        """Update the vote count from the Vote table"""
        self.votes_received = Vote.objects.filter(candidate=self).count()
        self.save()

class Election(models.Model):
    name = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("Start date must be before end date")
    
    def is_voting_open(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date
    
    def has_ended(self):
        return timezone.now() > self.end_date

class Vote(models.Model):
    voter = models.ForeignKey(VoterProfile, on_delete=models.CASCADE)
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('voter', 'election')  # Prevent multiple votes in same election
    
    def __str__(self):
        return f"{self.voter.user.username} voted for {self.candidate.user.username}"
    
    def save(self, *args, **kwargs):
        # Update voter's has_voted status
        self.voter.has_voted = True
        self.voter.save()
        
        super().save(*args, **kwargs)
        
        # Update candidate's vote count
        self.candidate.update_vote_count()
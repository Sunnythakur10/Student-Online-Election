from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from voting.models import VoterProfile, CandidateProfile, Election

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for testing'
    
    def handle(self, *args, **options):
        # Create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            email='admin@example.com',
            defaults={
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Admin',
                'last_name': 'User'
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(f'Created admin user: admin@example.com / admin123')
        
        # Create sample voters
        voters_data = [
            ('voter1', 'voter1@example.com', 'Alice', 'Johnson'),
            ('voter2', 'voter2@example.com', 'Bob', 'Smith'),
            ('voter3', 'voter3@example.com', 'Carol', 'Davis'),
        ]
        
        for username, email, first_name, last_name in voters_data:
            user, created = User.objects.get_or_create(
                username=username,
                email=email,
                defaults={
                    'role': 'voter',
                    'first_name': first_name,
                    'last_name': last_name
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                voter_profile = VoterProfile.objects.create(
                    user=user,
                    email_verified=True
                )
                self.stdout.write(f'Created voter: {email} / password123')
        
        # Create sample candidates
        candidates_data = [
            ('candidate1', 'candidate1@example.com', 'David', 'Wilson', 'Improving student facilities and campus life.'),
            ('candidate2', 'candidate2@example.com', 'Emma', 'Brown', 'Focus on academic excellence and student support.'),
            ('candidate3', 'candidate3@example.com', 'Frank', 'Taylor', 'Enhancing extracurricular activities and sports.'),
        ]
        
        for username, email, first_name, last_name, manifesto in candidates_data:
            user, created = User.objects.get_or_create(
                username=username,
                email=email,
                defaults={
                    'role': 'candidate',
                    'first_name': first_name,
                    'last_name': last_name
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                candidate_profile = CandidateProfile.objects.create(
                    user=user,
                    manifesto=manifesto
                )
                self.stdout.write(f'Created candidate: {email} / password123')
        
        # Create sample election
        election, created = Election.objects.get_or_create(
            name='Student Council Election 2024',
            defaults={
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=7),
                'is_active': True
            }
        )
        if created:
            self.stdout.write(f'Created election: {election.name}')
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
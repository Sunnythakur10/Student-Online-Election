"""
Quick Demo Setup Script
Run this to create sample elections and candidates for demonstration
"""

from django.core.management.base import BaseCommand
from voting.models import CustomUser, Election, CandidateProfile
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Creates demo data for project demonstration'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating demo data...\n')

        # Create an active election
        election = Election.objects.create(
            title='Student Council Election 2025',
            description='Vote for your student representatives for the academic year 2025-26',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=3)
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created election: {election.title}'))

        # Create candidate users and profiles
        candidates_data = [
            {
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'email': 'alice.johnson@college.edu',
                'position': 'President',
                'slogan': 'Leading with Vision and Integrity',
                'manifesto': 'I promise to represent every student voice and work towards making our campus a better place for learning and growth.'
            },
            {
                'first_name': 'Bob',
                'last_name': 'Smith',
                'email': 'bob.smith@college.edu',
                'position': 'Vice President',
                'slogan': 'Unity and Progress Together',
                'manifesto': 'My goal is to bridge gaps between different departments and create a unified student community.'
            },
            {
                'first_name': 'Carol',
                'last_name': 'Davis',
                'email': 'carol.davis@college.edu',
                'position': 'Secretary',
                'slogan': 'Organized, Efficient, Reliable',
                'manifesto': 'I will ensure transparent communication and efficient management of all student affairs.'
            },
            {
                'first_name': 'David',
                'last_name': 'Wilson',
                'email': 'david.wilson@college.edu',
                'position': 'President',
                'slogan': 'Innovation for Tomorrow',
                'manifesto': 'Let\'s bring innovative solutions to campus problems and prepare for the future together.'
            }
        ]

        for data in candidates_data:
            # Create user
            username = f"{data['first_name'].lower()}.{data['last_name'].lower()}"
            
            # Check if user already exists
            if CustomUser.objects.filter(email=data['email']).exists():
                self.stdout.write(self.style.WARNING(f'⚠ User {data["email"]} already exists, skipping...'))
                continue
            
            user = CustomUser.objects.create_user(
                username=username,
                email=data['email'],
                role='candidate',
                first_name=data['first_name'],
                last_name=data['last_name']
            )
            
            # Create candidate profile
            CandidateProfile.objects.create(
                user=user,
                election=election,
                position=data['position'],
                slogan=data['slogan'],
                manifesto=data['manifesto']
            )
            
            self.stdout.write(self.style.SUCCESS(f'✓ Created candidate: {data["first_name"]} {data["last_name"]} ({data["position"]})'))

        # Create sample voters
        voters_data = [
            {'name': 'John Doe', 'email': 'john.doe@student.edu', 'branch': 'Computer Science', 'year': 2},
            {'name': 'Jane Smith', 'email': 'jane.smith@student.edu', 'branch': 'Mechanical Engineering', 'year': 3},
            {'name': 'Mike Brown', 'email': 'mike.brown@student.edu', 'branch': 'Electronics', 'year': 1},
        ]

        for data in voters_data:
            if CustomUser.objects.filter(email=data['email']).exists():
                self.stdout.write(self.style.WARNING(f'⚠ Voter {data["email"]} already exists, skipping...'))
                continue
            
            name_parts = data['name'].split()
            username = data['email'].split('@')[0]
            
            CustomUser.objects.create_user(
                username=username,
                email=data['email'],
                role='voter',
                first_name=name_parts[0],
                last_name=name_parts[1] if len(name_parts) > 1 else '',
                branch=data['branch'],
                year_of_study=data['year']
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created voter: {data["name"]}'))

        self.stdout.write(self.style.SUCCESS('\n✅ Demo data created successfully!'))
        self.stdout.write('\nYou can now:')
        self.stdout.write('  1. Login as admin: sunnyking8691@gmail.com')
        self.stdout.write('  2. Login as voter: john.doe@student.edu')
        self.stdout.write('  3. View candidates and cast votes')
        self.stdout.write('  4. Check results as admin\n')

from django.core.management.base import BaseCommand
from voting.models import LoginToken


class Command(BaseCommand):
    help = 'Clean up expired and used login tokens older than 7 days'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Delete tokens older than this many days (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Showing what would be deleted (tokens older than {days} days)'))
        
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Q
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Find tokens to delete
        tokens_to_delete = LoginToken.objects.filter(
            Q(expires_at__lt=timezone.now()) | Q(is_used=True),
            created_at__lt=cutoff_date
        )
        
        count = tokens_to_delete.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No tokens to clean up.'))
            return
        
        if dry_run:
            self.stdout.write(f'Would delete {count} tokens:')
            for token in tokens_to_delete[:10]:  # Show first 10
                status = 'used' if token.is_used else 'expired'
                self.stdout.write(f'  - {token.user.email}: {status}, created {token.created_at}')
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
        else:
            tokens_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} expired/used tokens.'))

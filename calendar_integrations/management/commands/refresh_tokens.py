from django.core.management.base import BaseCommand
from django.utils import timezone
from calendar_integrations.token_refresh import TokenRefreshManager
from calendar_integrations.models import CalendarIntegration
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Refresh expired calendar integration tokens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be refreshed without actually refreshing',
        )
        parser.add_argument(
            '--integration-id',
            type=str,
            help='Refresh token for a specific integration ID',
        )
        parser.add_argument(
            '--provider',
            type=str,
            choices=['google', 'outlook'],
            help='Refresh tokens for a specific provider only',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        integration_id = options.get('integration_id')
        provider = options.get('provider')

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting token refresh {'(DRY RUN)' if dry_run else ''}"
            )
        )

        try:
            refresh_manager = TokenRefreshManager()

            if integration_id:
                # Refresh specific integration
                try:
                    integration = CalendarIntegration.objects.get(id=integration_id)
                    self.refresh_single_integration(refresh_manager, integration, dry_run)
                except CalendarIntegration.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f"Integration {integration_id} not found")
                    )
                    return
            else:
                # Refresh all expired tokens
                self.refresh_all_expired(refresh_manager, provider, dry_run)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error during token refresh: {e}")
            )
            logger.error(f"Token refresh command failed: {e}")

    def refresh_single_integration(self, refresh_manager, integration, dry_run):
        """Refresh token for a single integration"""
        self.stdout.write(f"Processing integration {integration.id} ({integration.provider})")
        
        if dry_run:
            needs_refresh = refresh_manager._needs_refresh(integration)
            self.stdout.write(
                f"  - Needs refresh: {needs_refresh}"
            )
            if needs_refresh:
                self.stdout.write("  - Would refresh token")
        else:
            success = refresh_manager.refresh_integration_token(integration)
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f"  - Successfully refreshed token")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"  - Failed to refresh token")
                )

    def refresh_all_expired(self, refresh_manager, provider, dry_run):
        """Refresh all expired tokens"""
        # Get integrations that need refresh
        queryset = CalendarIntegration.objects.filter(status='active')
        
        if provider:
            queryset = queryset.filter(provider=provider)

        integrations = list(queryset)
        
        if not integrations:
            self.stdout.write("No active integrations found")
            return

        # Filter integrations that need refresh
        integrations_to_refresh = [
            integration for integration in integrations
            if refresh_manager._needs_refresh(integration)
        ]

        self.stdout.write(
            f"Found {len(integrations)} active integrations, "
            f"{len(integrations_to_refresh)} need token refresh"
        )

        if not integrations_to_refresh:
            self.stdout.write("No tokens need refreshing")
            return

        if dry_run:
            self.stdout.write("Integrations that would be refreshed:")
            for integration in integrations_to_refresh:
                expiry_str = integration.token_expiry.strftime('%Y-%m-%d %H:%M:%S') if integration.token_expiry else 'Unknown'
                self.stdout.write(
                    f"  - {integration.id} ({integration.provider}) - expires: {expiry_str}"
                )
        else:
            # Perform actual refresh
            successful = 0
            failed = 0

            for integration in integrations_to_refresh:
                self.stdout.write(f"Refreshing {integration.id} ({integration.provider})...")
                
                success = refresh_manager.refresh_integration_token(integration)
                if success:
                    successful += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  - Success")
                    )
                else:
                    failed += 1
                    self.stdout.write(
                        self.style.ERROR(f"  - Failed")
                    )

            # Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nToken refresh completed: {successful} successful, {failed} failed"
                )
            )

            if failed > 0:
                self.stdout.write(
                    self.style.WARNING(
                        "Some token refreshes failed. Check logs for details."
                    )
                )
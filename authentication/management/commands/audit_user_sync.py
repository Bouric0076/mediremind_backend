from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from authentication.services import AuthenticationService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Audit and fix Django-Supabase user synchronization issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Automatically fix synchronization issues (requires manual password input)',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Check specific user by email',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting Django-Supabase user synchronization audit...')
        )
        
        auth_service = AuthenticationService()
        
        try:
            from supabase_client import admin_client
            
            # Get all Supabase users
            supabase_users = admin_client.auth.admin.list_users()
            supabase_emails = {user.email for user in supabase_users}
            
            self.stdout.write(f"Found {len(supabase_users)} users in Supabase")
            
            # Get all Django users
            if options['email']:
                django_users = User.objects.filter(email=options['email'])
                if not django_users.exists():
                    raise CommandError(f"User with email {options['email']} not found in Django")
            else:
                django_users = User.objects.all()
            
            django_emails = {user.email for user in django_users}
            self.stdout.write(f"Found {len(django_users)} users in Django")
            
            # Find synchronization issues
            missing_in_supabase = django_emails - supabase_emails
            missing_in_django = supabase_emails - django_emails
            
            self.stdout.write("\n" + "="*50)
            self.stdout.write("SYNCHRONIZATION AUDIT RESULTS")
            self.stdout.write("="*50)
            
            # Users in Django but not in Supabase
            if missing_in_supabase:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n{len(missing_in_supabase)} users found in Django but NOT in Supabase:"
                    )
                )
                for email in missing_in_supabase:
                    self.stdout.write(f"  - {email}")
                    
                if options['fix'] and not options['dry_run']:
                    self.stdout.write("\nAttempting to fix missing Supabase users...")
                    self._fix_missing_supabase_users(missing_in_supabase, auth_service)
                elif options['dry_run']:
                    self.stdout.write(
                        self.style.NOTICE(
                            "\n[DRY RUN] Would attempt to create these users in Supabase"
                        )
                    )
            else:
                self.stdout.write(
                    self.style.SUCCESS("\n✓ All Django users exist in Supabase")
                )
            
            # Users in Supabase but not in Django
            if missing_in_django:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n{len(missing_in_django)} users found in Supabase but NOT in Django:"
                    )
                )
                for email in missing_in_django:
                    self.stdout.write(f"  - {email}")
                    
                if options['fix'] and not options['dry_run']:
                    self.stdout.write("\nAttempting to fix missing Django users...")
                    self._fix_missing_django_users(missing_in_django, supabase_users)
                elif options['dry_run']:
                    self.stdout.write(
                        self.style.NOTICE(
                            "\n[DRY RUN] Would attempt to create these users in Django"
                        )
                    )
            else:
                self.stdout.write(
                    self.style.SUCCESS("\n✓ All Supabase users exist in Django")
                )
            
            # Summary
            self.stdout.write("\n" + "="*50)
            self.stdout.write("AUDIT SUMMARY")
            self.stdout.write("="*50)
            
            if not missing_in_supabase and not missing_in_django:
                self.stdout.write(
                    self.style.SUCCESS("✓ All users are properly synchronized!")
                )
            else:
                total_issues = len(missing_in_supabase) + len(missing_in_django)
                self.stdout.write(
                    self.style.WARNING(f"⚠ Found {total_issues} synchronization issues")
                )
                
                if not options['fix']:
                    self.stdout.write(
                        self.style.NOTICE(
                            "\nRun with --fix to automatically resolve issues"
                        )
                    )
                    self.stdout.write(
                        self.style.NOTICE(
                            "Run with --dry-run to see what would be changed"
                        )
                    )
            
        except Exception as e:
            raise CommandError(f"Error during audit: {str(e)}")

    def _fix_missing_supabase_users(self, missing_emails, auth_service):
        """Fix users that exist in Django but not in Supabase"""
        for email in missing_emails:
            try:
                django_user = User.objects.get(email=email)
                
                # We can't create Supabase users without passwords
                # So we'll create them with a temporary password and require reset
                temp_password = f"TempPass{django_user.id}!"
                
                full_name = f"{django_user.first_name} {django_user.last_name}".strip()
                if not full_name:
                    full_name = email.split('@')[0]
                
                supabase_user = auth_service._create_supabase_user(
                    email, temp_password, full_name
                )
                
                if supabase_user:
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Created Supabase user: {email}")
                    )
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ User {email} should reset their password"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"✗ Failed to create Supabase user: {email}")
                    )
                    
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"✗ Django user not found: {email}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Error creating Supabase user {email}: {str(e)}")
                )

    def _fix_missing_django_users(self, missing_emails, supabase_users):
        """Fix users that exist in Supabase but not in Django"""
        for email in missing_emails:
            try:
                # Find the Supabase user
                supabase_user = next((u for u in supabase_users if u.email == email), None)
                
                if not supabase_user:
                    continue
                
                # Extract user info from Supabase
                full_name = supabase_user.user_metadata.get('full_name', '') if supabase_user.user_metadata else ''
                if not full_name:
                    full_name = email.split('@')[0]
                
                name_parts = full_name.split()
                first_name = name_parts[0] if name_parts else ''
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                
                # Create Django user
                with transaction.atomic():
                    django_user = User.objects.create_user(
                        username=email,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        is_active=True
                    )
                    
                    # Create a basic patient profile (default role)
                    from accounts.models import EnhancedPatient
                    from datetime import date
                    
                    # Create with minimal required fields
                    EnhancedPatient.objects.create(
                        user=django_user,
                        date_of_birth=date(1990, 1, 1),  # Default date, user should update
                        gender='P',  # Prefer not to say
                        phone='000-000-0000',  # Default phone, user should update
                        address_line1='Not provided',
                        city='Not provided',
                        state='Not provided',
                        zip_code='00000',
                        emergency_contact_name='Not provided',
                        emergency_contact_relationship='Not provided',
                        emergency_contact_phone='000-000-0000'
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Created Django user: {email}")
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Error creating Django user {email}: {str(e)}")
                )
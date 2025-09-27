# Generated migration for token encryption

from django.db import migrations, models
from django.db.migrations import RunPython


def encrypt_existing_tokens(apps, schema_editor):
    """
    Encrypt existing tokens in the database.
    """
    CalendarIntegration = apps.get_model('calendar_integrations', 'CalendarIntegration')
    
    # Import encryption functions
    try:
        from calendar_integrations.encryption import encrypt_token
        
        for integration in CalendarIntegration.objects.all():
            # Encrypt access token if it exists and isn't already encrypted
            if integration.access_token:
                try:
                    # Try to decrypt first to check if already encrypted
                    from calendar_integrations.encryption import decrypt_token
                    decrypt_token(integration.access_token)
                    # If no exception, it's already encrypted
                    continue
                except:
                    # Not encrypted, so encrypt it
                    integration.access_token = encrypt_token(integration.access_token)
            
            # Encrypt refresh token if it exists and isn't already encrypted
            if integration.refresh_token:
                try:
                    decrypt_token(integration.refresh_token)
                    # If no exception, it's already encrypted
                    continue
                except:
                    # Not encrypted, so encrypt it
                    integration.refresh_token = encrypt_token(integration.refresh_token)
            
            integration.save()
            
    except ImportError:
        # Skip encryption if encryption module not available
        pass


def decrypt_existing_tokens(apps, schema_editor):
    """
    Decrypt tokens back to plain text (reverse migration).
    """
    CalendarIntegration = apps.get_model('calendar_integrations', 'CalendarIntegration')
    
    try:
        from calendar_integrations.encryption import decrypt_token
        
        for integration in CalendarIntegration.objects.all():
            # Decrypt access token if it exists
            if integration.access_token:
                try:
                    decrypted = decrypt_token(integration.access_token)
                    if decrypted:
                        integration.access_token = decrypted
                except:
                    # Already decrypted or invalid
                    pass
            
            # Decrypt refresh token if it exists
            if integration.refresh_token:
                try:
                    decrypted = decrypt_token(integration.refresh_token)
                    if decrypted:
                        integration.refresh_token = decrypted
                except:
                    # Already decrypted or invalid
                    pass
            
            integration.save()
            
    except ImportError:
        # Skip decryption if encryption module not available
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('calendar_integrations', '0001_initial'),
    ]

    operations = [
        # Rename existing fields to private fields
        migrations.RenameField(
            model_name='calendarintegration',
            old_name='access_token',
            new_name='_access_token',
        ),
        migrations.RenameField(
            model_name='calendarintegration',
            old_name='refresh_token',
            new_name='_refresh_token',
        ),
        
        # Update database column names to maintain compatibility
        migrations.AlterField(
            model_name='calendarintegration',
            name='_access_token',
            field=models.TextField(db_column='access_token'),
        ),
        migrations.AlterField(
            model_name='calendarintegration',
            name='_refresh_token',
            field=models.TextField(blank=True, null=True, db_column='refresh_token'),
        ),
        
        # Encrypt existing tokens
        RunPython(encrypt_existing_tokens, decrypt_existing_tokens),
    ]
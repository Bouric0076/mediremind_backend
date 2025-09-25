#!/usr/bin/env python
"""
Script to clear Django migration tracking table in Supabase database
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from django.db import connection

def clear_migration_table():
    """Clear the django_migrations table to start fresh"""
    try:
        with connection.cursor() as cursor:
            # Check if django_migrations table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'django_migrations'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                print("Found django_migrations table. Clearing it...")
                cursor.execute("DELETE FROM django_migrations;")
                print("✅ Successfully cleared django_migrations table")
            else:
                print("ℹ️  django_migrations table doesn't exist yet")
            
            # Also clear any existing tables to start completely fresh
            print("\nDropping all existing tables...")
            cursor.execute("""
                DROP SCHEMA public CASCADE;
                CREATE SCHEMA public;
                GRANT ALL ON SCHEMA public TO postgres;
                GRANT ALL ON SCHEMA public TO public;
            """)
            print("✅ Successfully dropped and recreated public schema")
            
    except Exception as e:
        print(f"❌ Error clearing migration table: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧹 Clearing Django migration tracking table in Supabase...")
    success = clear_migration_table()
    if success:
        print("\n✅ Migration table cleared successfully!")
        print("You can now run: python manage.py makemigrations")
        print("Then: python manage.py migrate")
    else:
        print("\n❌ Failed to clear migration table")
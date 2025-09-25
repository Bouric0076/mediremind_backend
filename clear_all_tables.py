#!/usr/bin/env python
"""
Script to identify and delete all tables in Supabase database
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

from django.db import connection

def get_all_tables():
    """Get list of all tables in the database"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        return [row[0] for row in cursor.fetchall()]

def delete_all_tables():
    """Delete all tables from the database"""
    try:
        tables = get_all_tables()
        
        if not tables:
            print("ℹ️  No tables found in the database")
            return True
            
        print(f"📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")
        
        print("\n🗑️  Deleting all tables...")
        
        with connection.cursor() as cursor:
            # Disable foreign key checks temporarily
            cursor.execute("SET session_replication_role = replica;")
            
            # Drop all tables
            for table in tables:
                try:
                    cursor.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE;')
                    print(f"  ✅ Deleted table: {table}")
                except Exception as e:
                    print(f"  ❌ Error deleting table {table}: {e}")
            
            # Re-enable foreign key checks
            cursor.execute("SET session_replication_role = DEFAULT;")
            
        # Verify all tables are deleted
        remaining_tables = get_all_tables()
        if remaining_tables:
            print(f"\n⚠️  Warning: {len(remaining_tables)} tables still remain:")
            for table in remaining_tables:
                print(f"  - {table}")
            return False
        else:
            print("\n✅ Successfully deleted all tables!")
            return True
            
    except Exception as e:
        print(f"❌ Error deleting tables: {e}")
        return False

def reset_sequences():
    """Reset all sequences in the database"""
    try:
        with connection.cursor() as cursor:
            # Get all sequences
            cursor.execute("""
                SELECT sequence_name 
                FROM information_schema.sequences 
                WHERE sequence_schema = 'public';
            """)
            sequences = [row[0] for row in cursor.fetchall()]
            
            if sequences:
                print(f"\n🔄 Resetting {len(sequences)} sequences...")
                for seq in sequences:
                    try:
                        cursor.execute(f'DROP SEQUENCE IF EXISTS "{seq}" CASCADE;')
                        print(f"  ✅ Deleted sequence: {seq}")
                    except Exception as e:
                        print(f"  ❌ Error deleting sequence {seq}: {e}")
            else:
                print("\nℹ️  No sequences found to reset")
                
    except Exception as e:
        print(f"❌ Error resetting sequences: {e}")

if __name__ == "__main__":
    print("🧹 Clearing all tables from Supabase database...")
    print("=" * 50)
    
    # First, list all tables
    tables = get_all_tables()
    
    if tables:
        print(f"📊 Database contains {len(tables)} tables")
        
        # Delete all tables
        success = delete_all_tables()
        
        # Reset sequences
        reset_sequences()
        
        if success:
            print("\n" + "=" * 50)
            print("✅ Database successfully cleared!")
            print("You can now run fresh migrations:")
            print("  1. python manage.py makemigrations")
            print("  2. python manage.py migrate")
        else:
            print("\n" + "=" * 50)
            print("❌ Some tables could not be deleted")
    else:
        print("✅ Database is already empty!")

# MANUAL DATABASE RESET INSTRUCTIONS

## Option 1: Using Supabase Dashboard (Recommended)
1. Open your Supabase project dashboard
2. Go to "SQL Editor" in the left sidebar
3. Create a new query
4. Copy and paste the contents of 'reset_database_schema.sql'
5. Click "Run" to execute

## Option 2: Using Supabase CLI (if installed)
```bash
supabase db reset
```

## What gets reset:
- All existing tables: users, patients, staff_profiles, appointments, push_subscriptions
- All data in these tables
- All sequences and auto-increment counters
- All custom functions (if any)

## After reset:
- Database will be completely empty
- You'll need to run Django migrations to recreate tables
- You'll need to create a new superuser account

## Next steps after reset:
1. Run Django migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. Create superuser:
   ```bash
   python manage.py createsuperuser
   ```

3. Load any initial data if needed

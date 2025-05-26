# supabase_client.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")  # anon key for auth
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # service role key for admin operations

# Regular client for auth and user operations
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Admin client with service role key for database operations
admin_client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

__all__ = ['supabase', 'admin_client']

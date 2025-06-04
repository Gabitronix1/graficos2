import os
from supabase import create_client, Client

def get_client() -> Client:
    """Return a Supabase client using URL and KEY from env variables"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE")
    if not url or not key:
        raise ValueError("SUPABASE_URL or SUPABASE_SERVICE_ROLE not set")
    return create_client(url, key)
